import pandas as pd
import numpy as np

from app.metrics.trend import r2


class MomentumScanner:
    def __init__(self, provider):
        self.provider = provider

    def scan(self, tickers):
        data = self.provider.download(tickers)

        rows = []

        for ticker, df in data.items():

            if len(df) < 60:
                continue

            close = df["Close"]
            volume = df["Volume"]

            # --- metrics ---

            # return (ostatnie 2h ~120 świec)
            ret = close.iloc[-1] / close.iloc[-120] - 1 if len(close) > 120 else 0

            # volume spike
            vol_ratio = volume.iloc[-1] / volume.tail(30).mean()

            # trend
            trend_score = r2(close.tail(120))

            # compression
            vol = close.pct_change().tail(30).std()

            rows.append({
                "ticker": ticker,
                "return": ret,
                "volume_ratio": vol_ratio,
                "trend": trend_score,
                "volatility": vol,
            })

        df = pd.DataFrame(rows)

        if df.empty:
            return df

        # --- percentyle ---
        df["rs_score"] = df["return"].rank(pct=True)
        df["volume_score"] = df["volume_ratio"].rank(pct=True)
        df["trend_score"] = df["trend"].rank(pct=True)

        # low vol = good compression
        df["compression_score"] = 1 - df["volatility"].rank(pct=True)

        df["score"] = (
            0.4 * df["rs_score"]
            + 0.2 * df["volume_score"]
            + 0.2 * df["trend_score"]
            + 0.2 * df["compression_score"]
        )

        return df.sort_values("score", ascending=False)
