import yfinance as yf
import time
import random
import pandas as pd

from app.providers.cache import load_cache, save_cache

def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]

def normalize_df(df, ticker=None):

    if isinstance(df.columns, pd.MultiIndex):

        if len(df.columns.levels[0]) == 1:
            df.columns = df.columns.droplevel(0)

        elif ticker is not None:
            df = df[ticker]

    return df

def has_ticker(data, ticker):

    if isinstance(data.columns, pd.MultiIndex):
        return ticker in data.columns.get_level_values(0)

    return True

class YahooProvider:

    def download(self, tickers, interval="30m", period="5d"):

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

        for chunk in chunked(to_download, 5): 

            try:
                data = yf.download(
                    tickers=chunk,
                    interval=interval,
                    period=period,
                    threads=False,
                    auto_adjust=True,
                    progress=False,
                )

                if len(chunk) == 1:
                    df = normalize_df(data, chunk[0]).dropna()
                    if not df.empty:
                        result[chunk[0]] = df
                        save_cache(chunk[0], df)

                else:
                    for ticker in chunk: 
                        if not has_ticker(data, ticker):
                            print(f"Missing data for {ticker}")
                            continue
                            
                        df = normalize_df(data, ticker).dropna()
                        if not df.empty:
                            result[ticker] = df
                            save_cache(ticker, df)

                time.sleep(random.uniform(1.5, 3))

            except Exception as e:
                print("Yahoo error:", e)

        return result
