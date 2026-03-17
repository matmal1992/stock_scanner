import pandas as pd


def read_parquet(path):

    try:
        return pd.read_parquet(path)
    except Exception as e:
        print(f"Error reading {path.stem}: {e}")
        return None


def save_tickers(results, path):

    if not results:
        print("Brak tickerów do zapisania")
    else:
        print(f"Zapisywanie {len(results)} tickerów...")

    tickers = []

    for ticker, _ in results:
        ticker_yf = ticker.replace("_", ".")
        tickers.append(ticker_yf)

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(",".join(tickers))

        print(f"Zapisano do: {path}")

    except Exception as e:
        print(f"Błąd zapisu pliku {path}: {e}")