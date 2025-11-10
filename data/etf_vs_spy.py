import json
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path

# === Load Data ===
input_file = Path("bill_etf_analysis_sector_relevant.json")
if not input_file.exists():
    raise FileNotFoundError("bill_etf_analysis_sector_relevant.json not found")

with open(input_file, "r", encoding="utf-8") as f:
    bills = json.load(f)

df = pd.DataFrame(bills)

# === Filter out neutral ===
df = df[df["label"] != "neutral"]

if df.empty:
    raise ValueError("No non-neutral bills found in dataset.")

# === Basic Summary ===
total_bills = len(df)
label_counts = df["label"].value_counts().to_dict()

print(f"\n📊 Total bills analyzed (excluding neutral): {total_bills}")
print("Label breakdown:")
for k, v in label_counts.items():
    print(f"  {k}: {v} ({v/total_bills:.1%})")

# === Average % Change by Sector & Sentiment ===
sector_summary = (
    df.groupby(["primary_sector", "label"])["price_change_pct"]
    .agg(["count", "mean"])
    .reset_index()
)
sector_summary.rename(columns={"mean": "avg_pct_change"}, inplace=True)

# === Fetch SPY baseline for same overall date range ===
start_date = min(datetime.strptime(d, "%Y-%m-%d") for d in df["enactment_date"])
end_date = max(datetime.strptime(d, "%Y-%m-%d") for d in df["enactment_date"]) + timedelta(days=30)

spy_data = yf.download("SPY", start=start_date, end=end_date, progress=False)
spy_start = float(spy_data["Close"].iloc[0])
spy_end = float(spy_data["Close"].iloc[-1])
spy_change = ((spy_end - spy_start) / spy_start) * 100

print(f"\n📈 SPY baseline change ({start_date.date()} → {end_date.date()}): {spy_change:+.2f}%")

# === Compare Each Sector/Label to SPY ===
sector_summary["vs_spy_diff"] = sector_summary["avg_pct_change"] - spy_change

# === Display Results ===
print("\nSector performance vs SPY (by sentiment):\n")
print(sector_summary.to_string(index=False, formatters={
    "avg_pct_change": "{:+.2f}%".format,
    "vs_spy_diff": "{:+.2f}%".format
}))

# === Save Summary ===
summary_file = Path("sector_sentiment_vs_spy.json")
sector_summary.to_json(summary_file, orient="records", indent=2)
print(f"\n✅ Summary saved to {summary_file}")

