import pandas as pd
from core.metrics import *
from core.io_utils import *
from report.report_updater import update_filter_section
from config import CONFIG_15M as CONFIG
from strategy_profiles import FILTERS

T2_COLUMNS = [
    ("Ticker", lambda i,t,m: t),
    ("1D Return", lambda i,t,m: f"{m['ret_1d']:.2%}"),
    ("R² Trend", lambda i,t,m: f"{m['trend_r2']:.2f}"),
    ("Volume Ratio", lambda i,t,m: f"{m['vol_ratio']:.2f}"),
    ("Compression", lambda i,t,m: f"{m['compression_ratio']:.2f}"),
    ("Dist From High", lambda i,t,m: f"{m['dist_from_high']:.2%}")
]

def calculate_metrics(df):

    if len(df) < 80:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    return {
        "ret_1d": return_pct(close, 26),
        "trend_r2": r2(close.tail(50)),
        "vol_ratio": volume_ratio(volume, 10, 50),
        "compression_ratio": compression_ratio(high, low, 5, 20),
        "dist_from_high": distance_from_high(close, 30)
    }

def scan_directory():

    candidates = []
    fail_stats = {
        "too_short_data": 0,
        "ret": 0,
        "trend": 0,
        "volume": 0,
        "compression": 0,
        "distance": 0
    }

    total_scanned = 0

    for path in CONFIG.data_dir.glob("*.parquet"):

        ticker = path.stem

        try:
            df = pd.read_parquet(path)
            metrics = calculate_metrics(df)

            if metrics is None:
                fail_stats["too_short_data"] += 1
                continue

            if metrics["ret_1d"] <= FILTERS.tier2.min_ret_1d:
                fail_stats["ret"] += 1
                continue

            if metrics["trend_r2"] <= FILTERS.tier2.min_trend_r2:
                fail_stats["trend"] += 1
                continue

            if metrics["vol_ratio"] <= FILTERS.tier2.min_vol_ratio:
                fail_stats["volume"] += 1
                continue

            if metrics["compression_ratio"] >= FILTERS.tier2.max_compression:
                fail_stats["compression"] += 1
                continue

            if metrics["dist_from_high"] <= FILTERS.tier2.min_dist_from_high:
                fail_stats["distance"] += 1
                continue

            candidates.append((ticker, metrics))

        except Exception as e:
            print(f"Błąd przy {ticker}: {e}")

    stats = {
        "total": total_scanned,
        "passed": len(candidates),
        "fails": fail_stats
    }

    return candidates, stats


def main():

    results, stats = scan_directory()
    update_filter_section(results, "<!-- T2_FILTER -->", T2_COLUMNS, stats)
    save_tickers(results, CONFIG.txt_dir / "third_tier_list.txt")

if __name__ == "__main__":
    main()