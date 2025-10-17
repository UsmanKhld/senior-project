import json
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Sector keyword mappings
SECTOR_KEYWORDS = {
    "healthcare": {
        "etf": "XLV",
        "keywords": ["health", "medical", "drug", "pharmaceutical", "medicare", "medicaid", 
                    "hospital", "patient", "disease", "clinical", "healthcare", "prescription",
                    "fda", "vaccine", "treatment", "therapy", "nursing"]
    },
    "technology": {
        "etf": "XLK",
        "keywords": ["technology", "tech", "software", "data", "cyber", "internet", "digital",
                    "ai", "artificial intelligence", "semiconductor", "computer", "algorithm",
                    "broadband", "5g", "telecom", "communications"]
    },
    "finance": {
        "etf": "XLF",
        "keywords": ["bank", "finance", "financial", "loan", "credit", "mortgage", "insurance",
                    "deposit", "banking", "investor", "securities", "investment", "capital",
                    "interest rate", "fed", "federal reserve"]
    },
    "energy": {
        "etf": "XLE",
        "keywords": ["energy", "oil", "gas", "petroleum", "fossil fuel", "renewable", "solar",
                    "wind", "coal", "fuel", "power plant", "utility", "electric"]
    },
    "consumer": {
        "etf": "XLY",
        "keywords": ["consumer", "retail", "store", "shop", "purchase", "sales", "product",
                    "brand", "restaurant", "food service", "advertising", "e-commerce"]
    },
    "industrials": {
        "etf": "XLI",
        "keywords": ["manufacturing", "industrial", "factory", "construction", "infrastructure",
                    "machinery", "transport", "airline", "defense", "aerospace", "railroad"]
    },
    "materials": {
        "etf": "XLB",
        "keywords": ["material", "chemical", "mining", "metal", "steel", "commodity", "agriculture",
                    "cement", "paper", "plastic"]
    }
}

def predict_sectors(bill_text):
    """Predict sectors based on keyword matching in bill text"""
    text_lower = bill_text.lower()
    sector_scores = defaultdict(int)
    
    for sector, data in SECTOR_KEYWORDS.items():
        for keyword in data["keywords"]:
            # Count occurrences of keyword
            sector_scores[sector] += text_lower.count(keyword)
    
    # Return sectors with scores > 0, sorted by score
    return sorted([(s, score) for s, score in sector_scores.items() if score > 0], 
                  key=lambda x: x[1], reverse=True)

def get_etf_prices(etf_ticker, date_str, days_after=30):
    """Fetch ETF price on date and X days after"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        end_date = date_obj + timedelta(days=days_after+30)
        
        # Download data
        data = yf.download(etf_ticker, start=date_obj, end=end_date, progress=False)
        
        if data.empty:
            return None, None, None
        
        # Get price on enactment date (find closest trading day)
        price_on_date = None
        actual_date = None
        for i in range(10):  # Look up to 10 days forward for first trading day
            check_date = date_obj + timedelta(days=i)
            if check_date in data.index:
                price_on_date = float(data.loc[check_date, "Close"])
                actual_date = check_date
                break
        
        if price_on_date is None:
            return None, None, None
        
        # Get price X days after
        future_date_obj = date_obj + timedelta(days=days_after)
        future_price = None
        for i in range(30):  # Look up to 30 days forward for price
            check_date = future_date_obj + timedelta(days=i)
            if check_date in data.index:
                future_price = float(data.loc[check_date, "Close"])
                break
        
        if future_price is None:
            return None, None, None
        
        price_change = ((future_price - price_on_date) / price_on_date) * 100
        return price_on_date, future_price, price_change
        
    except Exception as e:
        print(f"  Error fetching ETF data for {etf_ticker}: {e}")
        return None, None, None

def main():
    # Load cleaned bills
    input_file = Path("bills_cleaned.json")
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        print("Make sure you've run the cleaning script first")
        return
    
    print(f"Loading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        bills = json.load(f)
    
    print(f"Processing {len(bills)} bills...\n")
    
    results = []
    
    for i, bill in enumerate(bills, 1):
        print(f"[{i}/{len(bills)}] {bill['bill_type']}-{bill['bill_number']}: {bill['title'][:50]}...")
        
        # Predict sectors
        sectors = predict_sectors(bill.get("text", ""))
        if not sectors:
            print(f"  No sectors matched, skipping")
            continue
        
        top_sector, score = sectors[0]
        etf_ticker = SECTOR_KEYWORDS[top_sector]["etf"]
        
        print(f"  Top sector: {top_sector} ({etf_ticker}) - score: {score}")
        
        # Get ETF prices
        enactment_date = bill.get("latest_action_date")
        if not enactment_date:
            print(f"  No enactment date, skipping")
            continue
        
        price_on_date, future_price, price_change = get_etf_prices(etf_ticker, enactment_date)
        
        if price_on_date is None:
            print(f"  Could not fetch ETF data")
            continue
        
        # Determine label
        if price_change > 2:
            label = "positive"
        elif price_change < -2:
            label = "negative"
        else:
            label = "neutral"
        
        print(f"  {etf_ticker} price: ${price_on_date:.2f} → ${future_price:.2f} ({price_change:+.2f}%) [{label}]")
        
        result = {
            "bill_number": bill["bill_number"],
            "bill_type": bill["bill_type"],
            "title": bill["title"],
            "enactment_date": enactment_date,
            "predicted_sector": top_sector,
            "sector_score": score,
            "etf_ticker": etf_ticker,
            "price_on_date": round(price_on_date, 2),
            "price_30d_later": round(future_price, 2),
            "price_change_pct": round(price_change, 2),
            "label": label,
            "all_sectors": [(s, sc) for s, sc in sectors]
        }
        
        results.append(result)
    
    # Save results
    output_file = Path("bill_etf_analysis.json")
    print(f"\nSaving results to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    # Print summary stats
    print(f"\n=== Summary ===")
    print(f"Analyzed: {len(results)} bills")
    positive = sum(1 for r in results if r["label"] == "positive")
    negative = sum(1 for r in results if r["label"] == "negative")
    neutral = sum(1 for r in results if r["label"] == "neutral")
    print(f"Positive: {positive}, Negative: {negative}, Neutral: {neutral}")

if __name__ == "__main__":
    main()