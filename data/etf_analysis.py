import json
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path

SECTOR_ETF = {
    "healthcare": "XLV",
    "technology": "XLK",
    "finance": "XLF",
    "energy": "XLE",
    "consumer": "XLY",
    "industrials": "XLI",
    "materials": "XLB"
}

def get_etf_prices(etf_ticker, date_str):
    """Compare ETF price one month before and one month after a bill date."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        start_date = date_obj - timedelta(days=45)
        end_date = date_obj + timedelta(days=45)

        data = yf.download(etf_ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return None, None, None

        before_price = None
        after_price = None

        # Before (30 days prior)
        for i in range(30, 0, -1):
            check_date = date_obj - timedelta(days=i)
            if check_date in data.index:
                before_price = float(data.loc[check_date, "Close"])
                break

        # After (30 days later)
        for i in range(1, 31):
            check_date = date_obj + timedelta(days=i)
            if check_date in data.index:
                after_price = float(data.loc[check_date, "Close"])
                break

        if before_price is None or after_price is None:
            return None, None, None

        price_change = ((after_price - before_price) / before_price) * 100
        return before_price, after_price, price_change

    except Exception as e:
        print(f"  Error fetching ETF data for {etf_ticker}: {e}")
        return None, None, None

def main():
    input_file = Path("bills_sector_relevant.json")
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        bills = json.load(f)

    print(f"Processing {len(bills)} sector-relevant bills...\n")
    results = []

    for i, bill in enumerate(bills, 1):
        print(f"[{i}/{len(bills)}] {bill['bill_type']}-{bill['bill_number']}: {bill['title'][:60]}...")

        llm_analysis = bill.get("llm_analysis", "")
        parts = [p.strip().lower() for p in llm_analysis.split(",")]
        
        # Expecting: "RELEVANT, sector" or "relevant, sector"
        if len(parts) < 2:
            print("  Skipping — invalid llm_analysis format")
            continue

        status, primary_sector = parts[0], parts[1]
        
        # Should be "relevant"
        if status != "relevant":
            print(f"  Skipping — status is '{status}' (expected 'relevant')")
            continue

        etf_ticker = SECTOR_ETF.get(primary_sector)
        if not etf_ticker:
            print(f"  Unknown sector '{primary_sector}', skipping")
            continue

        enactment_date = bill.get("latest_action_date")
        if not enactment_date:
            print("  No enactment date, skipping")
            continue

        before_price, after_price, price_change = get_etf_prices(etf_ticker, enactment_date)
        if before_price is None:
            print("  Could not fetch ETF data")
            continue

        # Label by +/- 2% threshold
        if price_change > 2:
            label = "positive"
        elif price_change < -2:
            label = "negative"
        else:
            label = "neutral"

        print(f"  {etf_ticker} price: ${before_price:.2f} → ${after_price:.2f} ({price_change:+.2f}%) [{label}]")

        results.append({
            "bill_number": bill["bill_number"],
            "bill_type": bill["bill_type"],
            "title": bill["title"],
            "enactment_date": enactment_date,
            "primary_sector": primary_sector,
            "etf_ticker": etf_ticker,
            "price_month_before": round(before_price, 2),
            "price_month_after": round(after_price, 2),
            "price_change_pct": round(price_change, 2),
            "label": label
        })

    output_file = Path("bill_etf_analysis_sector_relevant.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ Saved analysis to {output_file}")
    print(f"Total analyzed: {len(results)}")
    
    # Print summary stats
    if results:
        positive = sum(1 for r in results if r["label"] == "positive")
        negative = sum(1 for r in results if r["label"] == "negative")
        neutral = sum(1 for r in results if r["label"] == "neutral")
        print(f"\nLabel distribution:")
        print(f"  Positive: {positive} ({positive/len(results)*100:.1f}%)")
        print(f"  Negative: {negative} ({negative/len(results)*100:.1f}%)")
        print(f"  Neutral:  {neutral} ({neutral/len(results)*100:.1f}%)")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
