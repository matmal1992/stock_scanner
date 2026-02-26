import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("15min/15min_gpw_data")


def r2(series):
    y = series.values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    return 1 - ss_res / ss_tot if ss_tot != 0 else 0


def calculate_metrics(df):

    # minimum 3 dni danych (~75 świec)
    if len(df) < 80:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # --- 1D intraday return (~26 świec) ---
    ret_1d = close.iloc[-1] / close.iloc[-26] - 1

    # --- intraday trend (R² z 50 świec) ---
    trend_r2 = r2(close.tail(50))

    # --- volume expansion ---
    vol_short = volume.tail(10).mean()
    vol_long = volume.tail(50).mean()
    vol_ratio = vol_short / vol_long if vol_long != 0 else 0

    # --- compression ---
    range_20 = (high - low).rolling(20).mean().iloc[-1]
    range_5 = (high - low).rolling(5).mean().iloc[-1]
    compression_ratio = range_5 / range_20 if range_20 != 0 else 1

    # --- distance from 30-bar high ---
    high_30 = close.rolling(30).max().iloc[-1]
    dist_from_high = close.iloc[-1] / high_30 - 1

    return {
        "ret_1d": ret_1d,
        "trend_r2": trend_r2,
        "vol_ratio": vol_ratio,
        "compression_ratio": compression_ratio,
        "dist_from_high": dist_from_high,
    }


def scan_directory():

    candidates = []

    for path in DATA_DIR.glob("*.parquet"):

        ticker = path.stem

        try:
            df = pd.read_parquet(path)
            metrics = calculate_metrics(df)

            if metrics is None:
                continue

            # --- FILTR 15M ---
            if (
                metrics["ret_1d"] > 0.02
                and metrics["trend_r2"] > 0.4
                and metrics["vol_ratio"] > 1.5
                and metrics["compression_ratio"] < 0.7
                and metrics["dist_from_high"] > -0.03
            ):
                candidates.append((ticker, metrics))

        except Exception as e:
            print(f"Błąd przy {ticker}: {e}")

    return candidates


def main():

    results = scan_directory()

    print("\n=== 15M SPEŁNIAJĄCE WARUNKI ===")
    print("-" * 70)

    for ticker, m in results:
        print(
            f"{ticker} | "
            f"Ret1D: {m['ret_1d']:.2%} | "
            f"R²: {m['trend_r2']:.2f} | "
            f"VolRatio: {m['vol_ratio']:.2f} | "
            f"Comp: {m['compression_ratio']:.2f} | "
            f"DistHigh: {m['dist_from_high']:.2%}"
        )

    print("-" * 70)
    print(f"Znaleziono: {len(results)} spółek")


if __name__ == "__main__":
    main()