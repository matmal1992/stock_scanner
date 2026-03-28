import numpy as np
import pandas as pd

# miejsce na definicję trendów, parametrów,
# np pod scalping, cfd, swing lub long term


def r2(series):
    y = series.values
    x = np.arange(len(y))

    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    return 1 - ss_res / ss_tot if ss_tot != 0 else 0


def atr(df, period=14):

    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    return atr.iloc[-1]


def compression_ratio(high, low, short=5, long=20):

    range_short = (high - low).rolling(short).mean().iloc[-1]
    range_long = (high - low).rolling(long).mean().iloc[-1]

    if range_long == 0:
        return 1

    return range_short / range_long


def volume_ratio(volume, short=10, long=30):

    vol_short = volume.tail(short).mean()
    vol_long = volume.tail(long).mean()

    if vol_long == 0:
        return 0

    return vol_short / vol_long


def distance_from_high(close, window):

    high_val = close.rolling(window).max().iloc[-1]

    return close.iloc[-1] / high_val - 1


def return_pct(close, bars):

    return close.iloc[-1] / close.iloc[-bars] - 1
