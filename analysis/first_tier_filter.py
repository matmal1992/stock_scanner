import pandas as pd
import numpy as np
from config import CONFIG_1D as CONFIG
from report.report_updater import update_filter_section
from strategy_profiles import FILTERS

def r2(series):
    y = series.values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    return 1 - ss_res / ss_tot if ss_tot != 0 else 0


def calculate_metrics(df):

    if len(df) < 60:
        return None

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
    compression_ratio = range_5 / range_20 if range_20 != 0 else 1

    return {
        "ret_20d": ret_20d,
        "trend_r2": trend_r2,
        "atr_pct": atr_pct,
        "avg_turnover": avg_turnover,
        "compression_ratio": compression_ratio,
    }

def save_tickers(results):

    tickers = []

    for ticker, _ in results:
        ticker_yf = ticker.replace("_", ".")
        tickers.append(ticker_yf)

    output_path = CONFIG.txt_dir / "second_tier_list.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(",".join(tickers))


def scan_directory():

    candidates = []
    fail_stats = {
        "ret": 0,
        "trend": 0,
        "atr": 0,
        "turnover": 0,
        "compression": 0
    }

    for path in CONFIG.data_dir.glob("*.parquet"):

        ticker = path.stem  # nazwa pliku bez .parquet

        try:
            df = pd.read_parquet(path)
            metrics = calculate_metrics(df)

            if metrics is None:
                continue

            # --- FILTR ---
            # if (
            #     metrics["ret_20d"] > FILTERS.tier1.min_ret_20d
            #     and metrics["trend_r2"] > FILTERS.tier1.min_trend_r2
            #     and metrics["atr_pct"] > FILTERS.tier1.min_atr_pct
            #     and metrics["avg_turnover"] > FILTERS.tier1.min_turnover
            #     and metrics["compression_ratio"] < FILTERS.tier1.max_compression
            # ):
            #     candidates.append((ticker, metrics))

            if metrics["ret_20d"] <= FILTERS.tier1.min_ret_20d:
                fail_stats["ret"] += 1
                continue

            if metrics["trend_r2"] <= FILTERS.tier1.min_trend_r2:
                fail_stats["trend"] += 1
                continue

            if metrics["atr_pct"] <= FILTERS.tier1.min_atr_pct:
                fail_stats["atr"] += 1
                continue

            if metrics["avg_turnover"] <= FILTERS.tier1.min_turnover:
                fail_stats["turnover"] += 1
                continue

            if metrics["compression_ratio"] >= FILTERS.tier1.max_compression:
                fail_stats["compression"] += 1
                continue

            candidates.append((ticker, metrics))

        except Exception as e:
            print(f"Błąd przy {ticker}: {e}")


    print("\nFilter statistics:")
    print(fail_stats)
    return candidates

def main():
    results = scan_directory()
    update_filter_section(results, "<!-- T1_FILTER -->", "first")
    save_tickers(results)
    
if __name__ == "__main__":
    main()


