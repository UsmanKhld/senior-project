import requests
import json
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("CONGRESS_API_KEY")
BASE_URL = "https://api.congress.gov/v3/bill"
NUM_BILLS_TO_FETCH = 50

if not API_KEY:
    raise ValueError("API_KEY not found in .env file")

def fetch_bills(limit=250, offset=0):
    """Fetch bills from the API"""
    params = {
        "api_key": API_KEY,
        "format": "json",
        "limit": min(limit, 250),  # API max is 250
        "offset": offset,
        "sort": "updateDate+desc"
    }
    
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def fetch_bill_details(bill_url):
    """Fetch detailed bill information from the bill URL"""
    params = {"api_key": API_KEY}
    response = requests.get(bill_url, params=params)
    response.raise_for_status()
    return response.json().get("bill", {})

def fetch_text_versions(bill_details):
    """Fetch the text versions URL"""
    text_versions_url = bill_details.get("textVersions", {}).get("url")
    if not text_versions_url:
        return None
    
    params = {"api_key": API_KEY}
    response = requests.get(text_versions_url, params=params)
    response.raise_for_status()
    return response.json().get("textVersions", [])

def get_html_text_url(text_versions):
    """Find the HTML formatted text URL from text versions"""
    if not text_versions:
        return None
    
    # Get the first (most recent) version
    latest_version = text_versions[0]
    formats = latest_version.get("formats", [])
    
    # Find the "Formatted Text" HTML version
    for fmt in formats:
        if fmt.get("type") == "Formatted Text":
            return fmt.get("url")
    
    return None

def fetch_bill_text(html_url):
    """Fetch and extract text from the HTML bill"""
    response = requests.get(html_url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)
    return text

def is_bill_enacted(bill_summary):
    """Check if a bill has been enacted (became public law)"""
    latest_action = bill_summary.get("latestAction", {})
    action_text = latest_action.get("text", "").lower()
    
    # Check for common "passed/enacted" indicators
    enacted_keywords = [
        "became public law",
        "enacted into law",
        "signed into law",
        "public law"
    ]
    
    return any(keyword in action_text for keyword in enacted_keywords)

# Main execution
def main():
    # Fetch bills based on NUM_BILLS_TO_FETCH constant using pagination
    print(f"Fetching up to {NUM_BILLS_TO_FETCH} enacted bills...")
    
    all_bills = []
    processed = 0
    offset = 0
    bills_needed = NUM_BILLS_TO_FETCH
    
    while len(all_bills) < NUM_BILLS_TO_FETCH:
        print(f"\nFetching batch starting at offset {offset}...")
        result = fetch_bills(limit=250, offset=offset)
        
        bills_batch = result.get("bills", [])
        if not bills_batch:
            print("No more bills available from API")
            break
        
        for i, bill_summary in enumerate(bills_batch, 1):
            # Check if we have enough bills
            if len(all_bills) >= NUM_BILLS_TO_FETCH:
                break
            
            # Check if bill is enacted before processing
            if not is_bill_enacted(bill_summary):
                print(f"  Skipping {bill_summary['type']}-{bill_summary['number']} (not enacted)")
                continue
            
            processed += 1
            
            try:
                print(f"\n[{processed}] Processing bill: {bill_summary['type']}-{bill_summary['number']}")
                print(f"    Title: {bill_summary['title'][:60]}...")
                
                # Step 2: Fetch bill details
                bill_details = fetch_bill_details(bill_summary["url"])
                
                # Step 3: Fetch text versions
                text_versions = fetch_text_versions(bill_details)
                
                # Step 4: Get HTML URL
                html_url = get_html_text_url(text_versions)
                
                if not html_url:
                    print(f"  ⚠ No HTML text version found, skipping")
                    continue
                
                # Step 5: Fetch and extract text
                print(f"  Fetching bill text...")
                bill_text = fetch_bill_text(html_url)
                
                # Step 6: Create final data structure
                bill_data = {
                    "congress": bill_summary["congress"],
                    "bill_number": bill_summary["number"],
                    "bill_type": bill_summary["type"],
                    "title": bill_summary["title"],
                    "origin_chamber": bill_summary["originChamber"],
                    "latest_action_date": bill_summary.get("latestAction", {}).get("actionDate"),
                    "latest_action_text": bill_summary.get("latestAction", {}).get("text"),
                    "update_date": bill_summary["updateDate"],
                    "url": bill_summary["url"],
                    "text": bill_text
                }
                
                all_bills.append(bill_data)
                print(f"  ✓ Successfully processed")
                
            except Exception as e:
                print(f"  ✗ Error processing bill: {e}")
                continue
        
        offset += 250
    
    # Save all bills to JSON
    with open("bills.json", "w", encoding="utf-8") as f:
        json.dump(all_bills, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Complete ===")
    print(f"Successfully fetched {len(all_bills)} enacted bills")
    print(f"Saved to bills.json")

if __name__ == "__main__":
    main()