import pandas as pd
import numpy as np
from config import CONFIG_15M as CONFIG
from report.report_updater import update_3T_filter_section
from config_filters import T3_FILTER

def r2(series):
    y = series.values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    return 1 - ss_res / ss_tot if ss_tot != 0 else 0


def calculate_atr(df, period=14):
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    return atr.iloc[-1]

def calculate_metrics(df):

    # At least 2 days of data (~150 candles)
    if len(df) < 150:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # Mikro-kompresja (1h vs 4h)
    range_12 = (high - low).rolling(12).mean().iloc[-1]   # 1h
    range_48 = (high - low).rolling(48).mean().iloc[-1]   # 4h
    compression_ratio = range_12 / range_48 if range_48 != 0 else 1

    # Bliskość high dnia
    session_high = high.iloc[-78:].max()  # ~1 sesja
    dist_from_high = close.iloc[-1] / session_high - 1

    # Breakout z ostatnich 20 świec (~100 min)
    breakout_level = high.tail(20).max()
    breakout = close.iloc[-1] > breakout_level

    # Ekspansja wolumenu (30 min vs 2.5h)
    vol_short = volume.tail(6).mean()
    vol_long = volume.tail(30).mean()
    vol_ratio = vol_short / vol_long if vol_long != 0 else 0

    # Mikro-trend (R² z 30 świec)
    trend_r2 = r2(close.tail(30))

    # ATR sanity check
    atr14 = calculate_atr(df, 14)
    last_candle_range = high.iloc[-1] - low.iloc[-1]
    atr_sanity = last_candle_range < 1.8 * atr14 if atr14 != 0 else False

    return {
        "compression_ratio": compression_ratio,
        "dist_from_high": dist_from_high,
        "breakout": breakout,
        "vol_ratio": vol_ratio,
        "trend_r2": trend_r2,
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
                metrics["compression_ratio"] < T3_FILTER.max_compression
                and metrics["dist_from_high"] > T3_FILTER.min_dist_from_high
                and metrics["breakout"] is True
                and metrics["vol_ratio"] > T3_FILTER.min_vol_ratio
                and metrics["trend_r2"] > T3_FILTER.min_trend_r2
                and metrics["atr_sanity"] is T3_FILTER.atr_sanity_required
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