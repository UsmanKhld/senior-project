import json
from pathlib import Path
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
import numpy as np

INPUT = "bill_sector_volatility_analysis.json"

def load_data():
    with open(INPUT, "r") as f:
        return json.load(f)

def compute_summary(data):
    summary = {}

    # Count anomaly types
    anomaly_counts = Counter([x["impact_classification"] for x in data])

    # Sector-level anomalies
    sector_anomalies = defaultdict(Counter)
    for x in data:
        sector_anomalies[x["sector"]][x["impact_classification"]] += 1
    
    # Accuracy summary
    accuracy_counts = Counter([x["prediction_correctness"] for x in data])

    # Z-score distribution
    z_scores = [x["z_score_deviation"] for x in data]

    summary["anomaly_counts"] = anomaly_counts
    summary["sector_anomalies"] = sector_anomalies
    summary["accuracy_counts"] = accuracy_counts
    summary["z_scores"] = z_scores
    summary["total_bills"] = len(data)

    return summary

def print_summary(summary):
    print("\n================ SUMMARY ================\n")
    print(f"Total bills analyzed: {summary['total_bills']}\n")

    print("Anomaly Classification:")
    for k, v in summary["anomaly_counts"].items():
        print(f"  {k}: {v} ({v/summary['total_bills']*100:.1f}%)")

    print("\nPrediction Accuracy:")
    for k, v in summary["accuracy_counts"].items():
        print(f"  {k}: {v} ({v/summary['total_bills']*100:.1f}%)")

    print("\nAnomalies by Sector:")
    for sector, counts in summary["sector_anomalies"].items():
        print(f"  {sector}: {dict(counts)}")

    print("\n=========================================\n")


def plot_anomaly_counts(summary):
    counts = summary["anomaly_counts"]
    labels = list(counts.keys())
    values = [counts[l] for l in labels]

    plt.figure(figsize=(7,5))
    plt.bar(labels, values)
    plt.title("Bill Impact Classification Counts")
    plt.ylabel("Number of Bills")
    plt.xlabel("Impact Category")
    plt.tight_layout()
    plt.savefig("anomaly_counts.png")
    plt.close()


def plot_sector_anomalies(summary):
    sector_data = summary["sector_anomalies"]

    sectors = list(sector_data.keys())
    major = [sector_data[s]["major_anomaly"] for s in sectors]
    moderate = [sector_data[s]["moderate_anomaly"] for s in sectors]
    normal = [sector_data[s]["normal_range"] for s in sectors]

    x = np.arange(len(sectors))
    width = 0.25

    plt.figure(figsize=(10,6))
    plt.bar(x - width, normal, width, label="Normal")
    plt.bar(x, moderate, width, label="Moderate")
    plt.bar(x + width, major, width, label="Major")

    plt.xticks(x, sectors)
    plt.ylabel("Count")
    plt.title("Sector-Level Impact Classification")
    plt.legend()
    plt.tight_layout()
    plt.savefig("sector_anomalies.png")
    plt.close()


def plot_zscore_distribution(summary):
    z = summary["z_scores"]

    plt.figure(figsize=(8,5))
    plt.hist(z, bins=20)
    plt.title("Distribution of Z-Score Deviations")
    plt.xlabel("Deviation (z-score)")
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.savefig("zscore_distribution.png")
    plt.close()


def main():
    data = load_data()
    summary = compute_summary(data)

    print_summary(summary)

    print("Generating plots...")
    plot_anomaly_counts(summary)
    plot_sector_anomalies(summary)
    plot_zscore_distribution(summary)
    print("Saved: anomaly_counts.png, sector_anomalies.png, zscore_distribution.png")


if __name__ == "__main__":
    main()
