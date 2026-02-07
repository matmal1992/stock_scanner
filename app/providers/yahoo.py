import yfinance as yf
import time
import random

from app.providers.cache import load_cache, save_cache


def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]


class YahooProvider:

    def download(self, tickers, interval="5m", period="5d"):

        result = {}
        to_download = []

        for ticker in tickers:

            cached = load_cache(ticker)

            if cached is not None:
                result[ticker] = cached
            else:
                to_download.append(ticker)

        if not to_download:
            return result

        for chunk in chunked(to_download, 8): 

            try:
                data = yf.download(
                    tickers=chunk,
                    interval=interval,
                    period=period,
                    group_by="ticker",
                    threads=False,
                    auto_adjust=True,
                    progress=False,
                )

                if len(chunk) == 1:
                    df = data.dropna()
                    if not df.empty:
                        result[chunk[0]] = df
                        save_cache(chunk[0], df)

                else:
                    for ticker in chunk:
                        df = data[ticker].dropna()

                        if not df.empty:
                            result[ticker] = df
                            save_cache(ticker, df)

                time.sleep(random.uniform(1.5, 3))

            except Exception as e:
                print("Yahoo error:", e)

        return result
