import pandas as pd

from stock_scanner.core.metrics import (
    atr,
    compression_ratio,
    distance_from_high,
    r2,
    return_pct,
    volume_ratio,
)


def metrics_t1(df: pd.DataFrame) -> dict[str, float] | None:
    if len(df) < 60:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    try:
        return {
            "ret_20d": return_pct(close, 20),
            "trend_r2": r2(close.tail(60)),
            "atr_pct": atr(df, 14) / close.iloc[-1],
            "avg_turnover": (close * volume).rolling(20).mean().iloc[-1],
            "compression_ratio": compression_ratio(high, low, 5, 20),
        }
    except (IndexError, ZeroDivisionError, ValueError) as e:
        print("metrics_t1 error:", e)
        return None


# zastanowić się czy na pewno lambdy to dobre rozwiązanie
T1_COLUMNS = [
    ("Ticker", lambda i, t, m: t),
    ("20D Return", lambda i, t, m: f"{m['ret_20d']:.2%}"),
    ("R² Trend", lambda i, t, m: f"{m['trend_r2']:.2f}"),
    ("ATR %", lambda i, t, m: f"{m['atr_pct']:.2%}"),
    ("Turnover", lambda i, t, m: f"{m['avg_turnover']:,.0f}"),
    ("Compression", lambda i, t, m: f"{m['compression_ratio']:.2f}"),
]


def metrics_t2(df: pd.DataFrame) -> dict[str, float] | None:
    if len(df) < 30:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    try:
        n = len(df)

        return {
            "ret_1d": return_pct(close, min(26, n)),
            "trend_r2": r2(close.tail(min(50, n))),
            "vol_ratio": volume_ratio(volume, min(10, n), min(40, n)),
            "compression_ratio": compression_ratio(high, low, 5, 20),
            "dist_from_high": distance_from_high(close, min(30, n)),
        }

    except Exception as e:
        print("metrics_t2 error:", e)
        return None


T2_COLUMNS = [
    ("Ticker", lambda i, t, m: t),
    ("1D Return", lambda i, t, m: f"{m['ret_1d']:.2%}"),
    ("R² Trend", lambda i, t, m: f"{m['trend_r2']:.2f}"),
    ("Volume Ratio", lambda i, t, m: f"{m['vol_ratio']:.2f}"),
    ("Compression", lambda i, t, m: f"{m['compression_ratio']:.2f}"),
    ("Dist From High", lambda i, t, m: f"{m['dist_from_high']:.2%}"),
]


def metrics_t3(df: pd.DataFrame) -> dict[str, float] | None:
    # if len(df) < 20:
    #     return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    try:
        n = len(df)
        print(f"T3 DEBUG: len={len(df)}")
        compression = compression_ratio(high, low, min(12, n // 4), min(48, n))

        session_high = high.iloc[-min(78, n) :].max()
        dist_high = close.iloc[-1] / session_high - 1

        breakout = close.iloc[-1] > high.tail(min(20, n)).max()
        vol_ratio = volume_ratio(volume, min(6, n), min(30, n))
        trend = r2(close.tail(min(30, n)))
        atr14 = atr(df, min(14, n))

        last_range = high.iloc[-1] - low.iloc[-1]
        atr_sanity = last_range < 1.8 * atr14 if atr14 != 0 else False

        alert = breakout and vol_ratio > 1.5 and trend > 0.2 and dist_high > -0.02

        return {
            "compression_ratio": compression,
            "dist_from_high": dist_high,
            "breakout": breakout,
            "vol_ratio": vol_ratio,
            "trend_r2": trend,
            "atr14": atr14,
            "atr_sanity": atr_sanity,
            "alert": alert,
        }

    except Exception as e:
        print("metrics_t3 error:", e)
        return None


T3_COLUMNS = [
    ("Rank", lambda i, t, m: i),
    ("Ticker", lambda i, t, m: t),
    ("Score", lambda i, t, m: f"{m['score']:.2f}"),
    ("Compression", lambda i, t, m: f"{m['compression_ratio']:.2f}"),
    ("Dist From High", lambda i, t, m: f"{m['dist_from_high']:.2%}"),
    ("Volume Ratio", lambda i, t, m: f"{m['vol_ratio']:.2f}"),
    ("R² Trend", lambda i, t, m: f"{m['trend_r2']:.2f}"),
    ("ATR", lambda i, t, m: f"{m['atr14']:.3f}"),
]
