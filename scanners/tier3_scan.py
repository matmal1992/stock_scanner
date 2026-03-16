from core.metrics import *
from core.io_utils import *
from config import CONFIG_15M as CONFIG
from report.report_updater import update_filter_section
from strategy_profiles import FILTERS

T3_COLUMNS = [
    ("Rank", lambda i,t,m: i),
    ("Ticker", lambda i,t,m: t),
    ("Score", lambda i,t,m: f"{m['score']:.2f}"),
    ("Compression", lambda i,t,m: f"{m['compression_ratio']:.2f}"),
    ("Dist From High", lambda i,t,m: f"{m['dist_from_high']:.2%}"),
    ("Volume Ratio", lambda i,t,m: f"{m['vol_ratio']:.2f}"),
    ("R² Trend", lambda i,t,m: f"{m['trend_r2']:.2f}"),
    ("ATR", lambda i,t,m: f"{m['atr14']:.3f}")
]

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

    fail_stats = {
        "too_short_data": 0,
        "compression": 0,
        "distance": 0,
        "breakout": 0,
        "volume": 0,
        "trend": 0,
        "atr_sanity": 0
    }

    total_scanned = 0

    for path in CONFIG.data_dir.glob("*.parquet"):

        ticker = path.stem
        total_scanned += 1

        try:
            df = read_parquet(path)
            if df is None:
                continue

            metrics = calculate_metrics(df)

            if metrics is None:
                fail_stats["too_short_data"] += 1
                continue

            if metrics["compression_ratio"] >= FILTERS.tier3.max_compression:
                fail_stats["compression"] += 1
                continue

            if metrics["dist_from_high"] <= FILTERS.tier3.min_dist_from_high:
                fail_stats["distance"] += 1
                continue

            if metrics["breakout"] is False:
                fail_stats["breakout"] += 1
                continue

            if metrics["vol_ratio"] <= FILTERS.tier3.min_vol_ratio:
                fail_stats["volume"] += 1
                continue

            if metrics["trend_r2"] <= FILTERS.tier3.min_trend_r2:
                fail_stats["trend"] += 1
                continue

            if metrics["atr_sanity"] is not FILTERS.tier3.atr_sanity_required:
                fail_stats["atr_sanity"] += 1
                continue

            score = calculate_score(metrics)
            metrics["score"] = score

            candidates.append((ticker, metrics))

        except Exception as e:
            print(f"Błąd przy {ticker}: {e}")

    candidates.sort(key=lambda x: x[1]["score"], reverse=True)

    stats = {
        "total": total_scanned,
        "passed": len(candidates),
        "fails": fail_stats
    }

    return candidates, stats

def calculate_score(m):

    score = (
        0.25 * (1 - m["compression_ratio"]) +   # im mniejsza kompresja tym lepiej
        0.25 * min(m["vol_ratio"] / 3, 1) +     # normalizacja volume expansion
        0.25 * m["trend_r2"] +                  # siła trendu
        0.25 * (1 + m["dist_from_high"])        # bliskość high
    )

    return score

def main():

    results, stats = scan_directory()
    update_filter_section(results, "<!-- T3_FILTER -->", T3_COLUMNS, stats)


if __name__ == "__main__":
    main()