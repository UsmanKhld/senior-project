import requests
import json
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("CONGRESS_API_KEY") 
BASE_URL = "https://api.congress.gov/v3/bill"
NUM_BILLS_TO_FETCH = 10

def fetch_bills(limit=1, offset=0):
    """Fetch bills from the API"""
    params = {
        "api_key": API_KEY,
        "format": "json",
        "limit": limit,
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

# Main execution
def main():
    # Fetch bills based on NUM_BILLS_TO_FETCH constant
    print(f"Fetching {NUM_BILLS_TO_FETCH} bills...")
    result = fetch_bills(limit=NUM_BILLS_TO_FETCH)
    
    if not result.get("bills"):
        print("No bills found")
        return
    
    all_bills = []
    
    for i, bill_summary in enumerate(result["bills"], 1):
        try:
            print(f"\n[{i}/{NUM_BILLS_TO_FETCH}] Processing bill: {bill_summary['type']}-{bill_summary['number']}")
            
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
    
    # Save all bills to JSON
    with open("bills.json", "w", encoding="utf-8") as f:
        json.dump(all_bills, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== Complete ===")
    print(f"Successfully fetched {len(all_bills)} bills")
    print(f"Saved to bills.json")

if __name__ == "__main__":
    main()