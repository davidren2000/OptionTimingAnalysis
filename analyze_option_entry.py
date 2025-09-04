import yfinance as yf
import pandas as pd
import numpy as np

def analyze_stock(symbol, start="2024-01-01", end="2025-09-01"):
    df = yf.download(symbol, start=start, end=end)
    df['Return'] = df['Close'].pct_change()
    df['CumulativeReturn'] = (1 + df['Return']).cumprod()
    
    # 1. Identify down streaks and cumulative return in streak
    df['IsDown'] = df['Return'] < 0
    df['DownStreak'] = df['IsDown'].groupby((df['IsDown'] != df['IsDown'].shift()).cumsum()).cumsum()
    df['DownStreakReturn'] = df['Return'].rolling(window=5, min_periods=1).sum().where(df['IsDown'])
    
    # 2. Drawdown from recent peak
    df['RecentPeak'] = df['Close'].cummax()
    df['Drawdown'] = (df['Close'] - df['Close'].cummax()) / df['Close'].cummax()
    
    # 3. Rebound probability after one-day drop
    df['NextDayReturn'] = df['Return'].shift(-1)
    bins = [-0.2, -0.1, -0.07, -0.05, -0.03, -0.01, 0, 0.01, 0.03, 0.05, 0.1, 0.2]
    df['TodayDropBin'] = pd.cut(df['Return'], bins)
    rebound_prob = df.groupby('TodayDropBin')['NextDayReturn'].apply(lambda x: (x > 0).mean())

    # 4. Drop fermentation: whether drop continues in following N days
    def fermentation_probability(drop_threshold, next_threshold, window=5):
        condition = df['Return'] <= -drop_threshold
        results = []
        for idx in df[condition].index:
            future_cum_return = df.loc[idx:].head(window)['Return'].cumsum()
            results.append((future_cum_return <= -next_threshold).any())
        return np.mean(results)

    fermentation_stats = {
        '5% to 7%': fermentation_probability(0.05, 0.07),
        '5% to 10%': fermentation_probability(0.05, 0.10),
        '7% to 10%': fermentation_probability(0.07, 0.10),
        '10% to 13%': fermentation_probability(0.10, 0.13),
    }

    # Print results
    print(f"\n===== Analyzing: {symbol} =====")
    print("📊 Next-day rebound probability by drop size:")
    print(rebound_prob)
    print("\n🔥 Drop fermentation probability:")
    for label, prob in fermentation_stats.items():
        print(f"{label}: {prob:.1%}")
    
    return df

# Example: run analysis on NVDA
df_nvda = analyze_stock("NVDA")
