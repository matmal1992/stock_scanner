import pandas as pd
from core.metrics import *
from core.io_utils import *
from report.report_updater import update_2T_filter_section
from config import CONFIG_15M as CONFIG
from strategy_profiles import FILTERS

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

    for path in CONFIG.data_dir.glob("*.parquet"):

        ticker = path.stem

        try:
            df = pd.read_parquet(path)
            metrics = calculate_metrics(df)

            if metrics is None:
                continue

            # --- FILTR 15M ---
            if (
                metrics["ret_1d"] > FILTERS.tier2.min_ret_1d
                and metrics["trend_r2"] > FILTERS.tier2.min_trend_r2
                and metrics["vol_ratio"] > FILTERS.tier2.min_vol_ratio
                and metrics["compression_ratio"] < FILTERS.tier2.max_compression
                and metrics["dist_from_high"] > FILTERS.tier2.min_dist_from_high
            ):
                candidates.append((ticker, metrics))

        except Exception as e:
            print(f"Błąd przy {ticker}: {e}")

    return candidates


def main():

    results = scan_directory()
    update_2T_filter_section(results, "<!-- T2_FILTER -->", "second")
    save_tickers(results, CONFIG.txt_dir / "third_tier_list.txt")


if __name__ == "__main__":
    main()