import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

# === Prompt user for tickers and time window ===
def get_tickers():
    print("Enter up to 5 ticker symbols, separated by commas (e.g. NVDA,HOOD,PLTR):")
    tickers = input("Tickers: ").upper().replace(" ", "").split(",")
    return tickers[:5] if tickers else []

def get_months_back():
    try:
        months = int(input("How many months of data to analyze (e.g. 6): "))
        return max(1, min(months, 24))  # clamp between 1 and 24 months
    except:
        return 6  # default fallback

# === User Inputs ===
TICKERS = get_tickers()
MONTHS_BACK = get_months_back()

# === Time Configuration ===
TODAY = datetime.today()
START_DATE = (TODAY - timedelta(days=30 * MONTHS_BACK)).strftime("%Y-%m-%d")
END_DATE = TODAY.strftime("%Y-%m-%d")

# === Constants ===
FERMENTATION_WINDOWS = [(0.05, 0.07), (0.05, 0.10), (0.07, 0.10), (0.10, 0.13)]
OUTPUT_FOLDER = "output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === Core Analysis Function ===
def analyze_stock(symbol, start=START_DATE, end=END_DATE):
    df = yf.download(symbol, start=start, end=end)
    if df.empty:
        print(f"[WARNING] No data found for {symbol}")
        return None, None

    df['Return'] = df['Close'].pct_change()
    df['CumulativeReturn'] = (1 + df['Return']).cumprod()

    # Down streaks
    df['IsDown'] = df['Return'] < 0
    df['DownStreak'] = df['IsDown'].groupby((df['IsDown'] != df['IsDown'].shift()).cumsum()).cumsum()
    df['DownStreakReturn'] = df['Return'].rolling(window=5, min_periods=1).sum().where(df['IsDown'])

    # Drawdown
    df['Drawdown'] = (df['Close'] - df['Close'].cummax()) / df['Close'].cummax()

    # Rebound probability
    df['NextDayReturn'] = df['Return'].shift(-1)
    bins = [-0.2, -0.1, -0.07, -0.05, -0.03, -0.01, 0, 0.01, 0.03, 0.05, 0.1, 0.2]
    df['TodayDropBin'] = pd.cut(df['Return'], bins)
    rebound_prob = df.groupby('TodayDropBin')['NextDayReturn'].apply(lambda x: (x > 0).mean())

    # Fermentation probability
    def fermentation_probability(drop_threshold, next_threshold, window=5):
        condition = df['Return'] <= -drop_threshold
        results = []
        for idx in df[condition].index:
            future_cum_return = df.loc[idx:].head(window)['Return'].cumsum()
            results.append((future_cum_return <= -next_threshold).any())
        return np.mean(results)

    fermentation_stats = {
        f"{int(a*100)}% to {int(b*100)}%": fermentation_probability(a, b)
        for (a, b) in FERMENTATION_WINDOWS
    }

    return rebound_prob, fermentation_stats

# === Main Analysis Loop ===
all_rebound = {}
all_ferment = {}

for ticker in TICKERS:
    print(f"\nAnalyzing: {ticker}...")
    rebound, ferment = analyze_stock(ticker)
    if rebound is None or ferment is None:
        continue

    all_rebound[ticker] = rebound
    all_ferment[ticker] = ferment

    # Save rebound to CSV
    rebound.to_csv(f"{OUTPUT_FOLDER}/{ticker}_rebound.csv")

    # Save fermentation to Markdown
    with open(f"{OUTPUT_FOLDER}/{ticker}_fermentation.md", "w") as f:
        f.write(f"# Drop Fermentation Probability for {ticker}\n\n")
        for k, v in ferment.items():
            f.write(f"- {k}: {v:.1%}\n")

    # Generate bar chart
    rebound.dropna().plot(kind='bar', title=f"{ticker} - Rebound Probability by Drop Size", figsize=(10, 5))
    plt.ylabel("Probability")
    plt.xlabel("Drop Bin")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_FOLDER}/{ticker}_rebound_chart.png")
    plt.close()

# === Save Combined Summary ===
combined_ferment = pd.DataFrame(all_ferment).T
combined_ferment.to_csv(f"{OUTPUT_FOLDER}/combined_fermentation_summary.csv")

print("\n✅ All results saved to ./output folder")
# === Save Combined Summary ===
combined_ferment = pd.DataFrame(all_ferment).T
combined_ferment.to_csv(f"{OUTPUT_FOLDER}/combined_fermentation_summary.csv")

# === Show Summary Chart ===
summary_fig, ax = plt.subplots(figsize=(10, 5))
combined_ferment.plot(kind='bar', ax=ax)
plt.title("Drop Fermentation Probability Summary")
plt.ylabel("Probability")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(f"{OUTPUT_FOLDER}/combined_summary_chart.png")
plt.show()

print("\n✅ Analysis complete. Summary chart has been displayed and saved in ./output")
