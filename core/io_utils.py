import pandas as pd


def read_parquet(path):

    try:
        return pd.read_parquet(path)
    except Exception as e:
        print(f"Error reading {path.stem}: {e}")
        return None


def save_tickers(results, path):

    tickers = []

    for ticker, _ in results:
        ticker_yf = ticker.replace("_", ".")
        tickers.append(ticker_yf)

    with open(path, "w", encoding="utf-8") as f:
        f.write(",".join(tickers))