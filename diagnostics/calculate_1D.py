from pathlib import Path

import numpy as np
import pandas as pd

# DATA_DIR = Path("data/1d")


def r2(series: pd.Series) -> float:
    y = series.values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    return 1 - ss_res / ss_tot if ss_tot != 0 else 0


def analyze_ticker(ticker: str) -> None:

    path = Path(f"{ticker}.parquet")

    if not path.exists():
        print("Brak danych dla", ticker)
        return

    df = pd.read_parquet(path)

    if len(df) < 60:
        print("Za mało danych")
        return

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # --- 20D return ---
    ret_20d = close.iloc[-1] / close.iloc[-20] - 1

    # --- R2 trend (60D) ---
    trend_r2 = r2(close.tail(60))

    # --- ATR(14) ---
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr14 = tr.rolling(14).mean().iloc[-1]
    atr_pct = atr14 / close.iloc[-1]

    # --- avg turnover ---
    avg_turnover = (close * volume).rolling(20).mean().iloc[-1]

    # --- compression ---
    range_20 = (high - low).rolling(20).mean().iloc[-1]
    range_5 = (high - low).rolling(5).mean().iloc[-1]
    compression_ratio = range_5 / range_20

    # --- distance from 20D high ---
    high_20 = close.rolling(20).max().iloc[-1]
    dist_from_high = close.iloc[-1] / high_20 - 1

    print(f"\nAnaliza: {ticker}")
    print("-" * 40)
    print(f"20D return: {ret_20d:.2%}")
    print(f"Trend R² (60D): {trend_r2:.3f}")
    print(f"ATR(14) %: {atr_pct:.2%}")
    print(f"Avg turnover (20D): {avg_turnover:,.0f}")
    print(f"Compression ratio: {compression_ratio:.2f}")
    print(f"Distance from 20D high: {dist_from_high:.2%}")
    print("-" * 40)


if __name__ == "__main__":
    analyze_ticker("CRI_WA")
