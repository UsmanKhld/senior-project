import matplotlib
matplotlib.use("TkAgg")
import json
import matplotlib.pyplot as plt
import numpy as np

# === Load results ===
with open("sector_sentiment_vs_spy.json", "r") as f:
    data = json.load(f)

# === Prepare data ===
# Extract unique sectors and keep positive/negative separated
sectors = sorted(list(set(d["primary_sector"].capitalize() for d in data)))
labels = ["positive", "negative"]

# Create lookup dicts for each metric
avg_change_lookup = {(d["primary_sector"].capitalize(), d["label"]): d["avg_pct_change"] for d in data}
vs_spy_lookup = {(d["primary_sector"].capitalize(), d["label"]): d["vs_spy_diff"] for d in data}

x = np.arange(len(sectors))
width = 0.35  # narrower for grouped bars

# === Chart 1: Average % Change ===
fig, ax = plt.subplots(figsize=(10, 6))

pos_values = [avg_change_lookup.get((s, "positive"), 0) for s in sectors]
neg_values = [avg_change_lookup.get((s, "negative"), 0) for s in sectors]

bars1 = ax.bar(x - width/2, pos_values, width, label="Positive Bills", color="mediumseagreen", edgecolor="black")
bars2 = ax.bar(x + width/2, neg_values, width, label="Negative Bills", color="indianred", edgecolor="black")

ax.axhline(0, color="gray", linewidth=1)
ax.set_title("Average % Change by Sector (Month Before → Month After Bill)")
ax.set_xticks(x)
ax.set_xticklabels(sectors, rotation=45)
ax.set_ylabel("Average % Change (%)")
ax.legend()

# Add data labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + (0.5 if height >= 0 else -1.5),
                f"{height:.2f}%", ha='center', fontsize=9)

plt.tight_layout()
plt.show()

# === Chart 2: Sector vs SPY ===
fig, ax = plt.subplots(figsize=(10, 6))

pos_vs_spy = [vs_spy_lookup.get((s, "positive"), 0) for s in sectors]
neg_vs_spy = [vs_spy_lookup.get((s, "negative"), 0) for s in sectors]

bars3 = ax.bar(x - width/2, pos_vs_spy, width, label="Positive Bills", color="mediumseagreen", edgecolor="black")
bars4 = ax.bar(x + width/2, neg_vs_spy, width, label="Negative Bills", color="indianred", edgecolor="black")

ax.axhline(0, color="gray", linewidth=1)
ax.set_title("Sector Performance vs SPY (by Bill Sentiment)")
ax.set_xticks(x)
ax.set_xticklabels(sectors, rotation=45)
ax.set_ylabel("Difference vs SPY (%)")
ax.legend()

# Add data labels
for bars in [bars3, bars4]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + (0.5 if height >= 0 else -1.5),
                f"{height:.2f}%", ha='center', fontsize=9)

plt.tight_layout()
plt.show()

