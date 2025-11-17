import json
import yfinance as yf
import numpy as np
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

def compute_sector_baseline(etf):
    """Compute mean and std of 30-day rolling changes for the ETF."""
    data = yf.download(etf, start="2010-01-01", end=datetime.today().strftime("%Y-%m-%d"), progress=False)

    closes = data["Close"].values
    changes = []

    for i in range(len(closes) - 30):
        before = closes[i]
        after = closes[i + 30]
        pct = ((after - before) / before) * 100
        changes.append(pct)

    return float(np.mean(changes)), float(np.std(changes))


def get_etf_movement(etf, date_str):
    """Get 1-month before and after prices."""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    start = date_obj - timedelta(days=40)
    end = date_obj + timedelta(days=40)

    data = yf.download(etf, start=start, end=end, progress=False)
    if data.empty:
        return None, None, None

    # find usable dates
    before_price = None
    after_price = None

    for i in range(30, 0, -1):
        d = date_obj - timedelta(days=i)
        if d in data.index:
            before_price = float(data.loc[d, "Close"])
            break

    for i in range(1, 31):
        d = date_obj + timedelta(days=i)
        if d in data.index:
            after_price = float(data.loc[d, "Close"])
            break

    if before_price is None or after_price is None:
        return None, None, None

    pct_change = ((after_price - before_price) / before_price) * 100
    return before_price, after_price, pct_change


def main():
    # load bills
    bills_path = Path("bills_sector_relevant.json")
    bills = json.load(open(bills_path, "r"))

    # Compute baselines for each sector
    baselines = {}
    for sector, etf in SECTOR_ETF.items():
        print(f"Computing baseline for {sector} ({etf})...")
        mean_change, std_change = compute_sector_baseline(etf)
        baselines[sector] = {"mean": mean_change, "std": std_change}

    results = []

    for bill in bills:
        llm = bill.get("llm_analysis", "").lower().strip()
        parts = [p.strip() for p in llm.split(",")]

        if len(parts) < 3:
            continue

        status, sector, predicted = parts[0], parts[1], parts[2]
        if status != "relevant":
            continue
        
        etf = SECTOR_ETF.get(sector)
        if not etf:
            continue

        date = bill.get("latest_action_date")
        if not date:
            continue

        before, after, actual_change = get_etf_movement(etf, date)
        if before is None:
            continue

        # baseline stats
        mean = baselines[sector]["mean"]
        std = baselines[sector]["std"]

        deviation = (actual_change - mean) / std

        # correctness
        if predicted == "positive" and actual_change > 2:
            correctness = "correct"
        elif predicted == "negative" and actual_change < -2:
            correctness = "correct"
        elif predicted == "neutral" and abs(actual_change) <= 2:
            correctness = "correct"
        else:
            correctness = "incorrect"

        results.append({
            "bill_title": bill["title"],
            "bill_type": bill["bill_type"],
            "bill_number": bill["bill_number"],
            "date": date,
            "sector": sector,
            "etf": etf,
            "predicted_sentiment": predicted,
            "price_before": before,
            "price_after": after,
            "actual_change_pct": actual_change,
            "sector_mean_change": mean,
            "sector_std_change": std,
            "z_score_deviation": deviation,
            "impact_classification": (
                "major_anomaly" if abs(deviation) > 2 else
                "moderate_anomaly" if abs(deviation) > 1 else
                "normal_range"
            ),
            "prediction_correctness": correctness
        })

    json.dump(results, open("bill_sector_volatility_analysis.json", "w"), indent=2)
    print("\nSaved → bill_sector_volatility_analysis.json")


if __name__ == "__main__":
    main()
