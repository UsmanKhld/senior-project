import json
import os
import time
import random
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GENAI_API_KEY")
if not API_KEY:
    raise ValueError("Missing GENAI_API_KEY in .env")

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-2.5-flash-lite"
INPUT_FILE = "bills_cleaned.json"
OUTPUT_FILE = "bills_sector_relevant.json"

def safe_generate_content(prompt, retries=5):
    """Make API request with exponential backoff for network errors"""
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            return response.text
        except Exception as e:
            msg = str(e)
            
            # Handle rate limiting
            if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
                wait = 15 + random.uniform(0, 5)
                print(f"⚠️ Rate limit hit. Waiting {wait:.1f}s...")
                time.sleep(wait)
            
            # Handle network errors (DNS, connection issues)
            elif "Temporary failure in name resolution" in msg or "connection" in msg.lower():
                wait = (2 ** attempt) + random.uniform(0, 3)  # exponential backoff
                print(f"⚠️ Network error (attempt {attempt+1}/{retries}). Waiting {wait:.1f}s...")
                time.sleep(wait)
            
            # Other errors
            else:
                print(f"❌ Unexpected error: {msg}")
                if attempt < retries - 1:
                    time.sleep(5)
                else:
                    return None
    
    print("❌ Skipping bill after repeated failures.")
    return None


def make_prompt(bill):
    return f"""
You are a policy analyst evaluating whether a U.S. bill has direct implications for specific economic sectors.

Analyze this bill and determine:
1. Does it have DIRECT policy implications for any sector? (regulations, funding, mandates, restrictions, incentives)
2. Which sector is MOST affected?
3. Is the bill likely to have a POSITIVE or NEGATIVE effect on that sector?

Respond ONLY in this exact format:
RELEVANT, [primary_sector], [positive|negative]
OR
NOT_RELEVANT

Valid sectors (choose ONE):
- healthcare
- technology
- finance
- energy
- consumer
- industrials
- materials

Examples:
- "Post office naming" → NOT_RELEVANT
- "FDA drug approval changes" → RELEVANT, healthcare, positive
- "Bank reserve requirements" → RELEVANT, finance, negative
- "Clean energy tax credits" → RELEVANT, energy, positive
- "Oil drilling restrictions" → RELEVANT, energy, negative

Bill title: {bill.get('title', 'Unknown')}
Bill text (first 4000 chars): {bill.get('text', '')[:4000]}

Your response:"""

def main():
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Missing {INPUT_FILE}")
    
    with open(INPUT_FILE, "r") as f:
        bills = json.load(f)
    
    print(f"Loaded {len(bills)} bills from {INPUT_FILE}\n")
    
    relevant_bills = []
    
    for i, bill in enumerate(bills, start=1):
        title = bill.get("title", "Unknown title")
        bill_id = f"{bill.get('bill_type','')}-{bill.get('bill_number','')}"
        
        print(f"[{i}/{len(bills)}] {bill_id}: {title[:60]}...")
        
        prompt = make_prompt(bill)
        response_text = safe_generate_content(prompt)
        
        # Skip if no response after retries
        if not response_text:
            print(f"  ⚠️ No response for bill {bill.get('bill_number')}")
            continue
        
        # Store LLM response
        response_clean = response_text.strip()
        bill["llm_analysis"] = response_clean
        
        print(f"  → {response_clean}")
        
        # Check if relevant
        if response_clean.upper().startswith("RELEVANT"):
            relevant_bills.append(bill)
            print("  ✅ Sector-relevant bill")
        else:
            print("  ➖ Not sector-relevant")
        
        # Rate limiting cooldown - add extra delay every 20 bills
        if i % 20 == 0:
            print(f"  💤 Checkpoint pause (processed {i} bills)...")
            time.sleep(10)
        else:
            time.sleep(6 + random.uniform(0, 2))
    
    # Save relevant bills
    with open(OUTPUT_FILE, "w") as f:
        json.dump(relevant_bills, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ Saved {len(relevant_bills)} sector-relevant bills to {OUTPUT_FILE}")
    print(f"   ({len(relevant_bills)/len(bills)*100:.1f}% of total bills)")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
