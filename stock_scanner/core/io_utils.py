from pathlib import Path

import pandas as pd


def read_parquet(path: Path) -> pd.DataFrame | None:

    try:
        return pd.read_parquet(path)
    except Exception as e:
        print(f"Error reading {path.stem}: {e}")
        return None


def save_tickers(results: list[tuple[str, None]], path: Path) -> None:

    if not results:
        print("Brak tickerów do zapisania")
    else:
        print(f"Zapisywanie {len(results)} tickerów...")

    tickers: list[str] = []

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


def load_tickers(txt_path: Path) -> list[str]:
    tickers: list[str] = []

    with open(txt_path, "r") as f:
        for line in f:
            parts = line.strip().split(",")

            for p in parts:
                t = p.strip()
                if t:
                    tickers.append(t)

    return tickers
