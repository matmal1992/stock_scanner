from config import CONFIG_1D, CONFIG_15M, CONFIG_5M
from config_filters import T1_FILTER, T2_FILTER, T3_FILTER
from core.metrics import *

# -------- TIER 1 --------

def metrics_t1(df):

    if len(df) < 60:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    return {
        "ret_20d": return_pct(close, 20),
        "trend_r2": r2(close.tail(60)),
        "atr_pct": atr(df, 14) / close.iloc[-1],
        "avg_turnover": (close * volume).rolling(20).mean().iloc[-1],
        "compression_ratio": compression_ratio(high, low, 5, 20)
    }


T1_COLUMNS = [
    ("Ticker", lambda i,t,m: t),
    ("20D Return", lambda i,t,m: f"{m['ret_20d']:.2%}"),
    ("R² Trend", lambda i,t,m: f"{m['trend_r2']:.2f}"),
    ("ATR %", lambda i,t,m: f"{m['atr_pct']:.2%}"),
    ("Turnover", lambda i,t,m: f"{m['avg_turnover']:,.0f}"),
    ("Compression", lambda i,t,m: f"{m['compression_ratio']:.2f}")
]


# -------- TIER 2 --------

def metrics_t2(df):

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


T2_COLUMNS = [
    ("Ticker", lambda i,t,m: t),
    ("1D Return", lambda i,t,m: f"{m['ret_1d']:.2%}"),
    ("R² Trend", lambda i,t,m: f"{m['trend_r2']:.2f}"),
    ("Volume Ratio", lambda i,t,m: f"{m['vol_ratio']:.2f}"),
    ("Compression", lambda i,t,m: f"{m['compression_ratio']:.2f}"),
    ("Dist From High", lambda i,t,m: f"{m['dist_from_high']:.2%}")
]


# -------- TIER 3 --------

def metrics_t3(df):

    if len(df) < 150:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    compression = compression_ratio(high, low, 12, 48)

    session_high = high.iloc[-78:].max()
    dist_high = close.iloc[-1] / session_high - 1

    breakout = close.iloc[-1] > high.tail(20).max()

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
        "atr_sanity": atr_sanity
    }


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