from core.metrics import *
from config import CONFIG_15M as CONFIG
from report.report_updater import update_3T_filter_section
from strategy_profiles import FILTERS

def calculate_metrics(df):

    if len(df) < 150:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    compression = compression_ratio(high, low, 12, 48)

    session_high = high.iloc[-78:].max()
    dist_high = close.iloc[-1] / session_high - 1

    breakout_level = high.tail(20).max()
    breakout = close.iloc[-1] > breakout_level

    vol_ratio = volume_ratio(volume, 6, 30)

    trend = r2(close.tail(30))

    atr14 = atr(df, 14)

    last_range = high.iloc[-1] - low.iloc[-1]

    atr_sanity = last_range < 1.8 * atr14 if atr14 != 0 else False

    return {
        "compression_ratio": compression,
        "dist_from_high": dist_high,
        "breakout": breakout,
        "vol_ratio": vol_ratio,
        "trend_r2": trend,
        "atr14": atr14,
        "last_close": close.iloc[-1],
        "atr_sanity": atr_sanity
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

            # Final 5m filter
            if (
                metrics["compression_ratio"] < FILTERS.tier3.max_compression
                and metrics["dist_from_high"] > FILTERS.tier3.min_dist_from_high
                and metrics["breakout"] is True
                and metrics["vol_ratio"] > FILTERS.tier3.min_vol_ratio
                and metrics["trend_r2"] > FILTERS.tier3.min_trend_r2
                and metrics["atr_sanity"] is FILTERS.tier3.atr_sanity_required
            ):
                score = calculate_score(metrics)
                metrics["score"] = score
                candidates.append((ticker, metrics))

        except Exception as e:
            print(f"Błąd przy {ticker}: {e}")

    candidates.sort(key=lambda x: x[1]["score"], reverse=True)
    return candidates

def calculate_score(m):

    score = (
        0.25 * (1 - m["compression_ratio"]) +   # im mniejsza kompresja tym lepiej
        0.25 * min(m["vol_ratio"] / 3, 1) +     # normalizacja volume expansion
        0.25 * m["trend_r2"] +                  # siła trendu
        0.25 * (1 + m["dist_from_high"])        # bliskość high
    )

    return score

def main():

    results = scan_directory()
    update_3T_filter_section(results, "<!-- T3_FILTER -->", "third")


if __name__ == "__main__":
    main()