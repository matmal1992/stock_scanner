import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

# Upewnić się czy wszystko tutaj jest w aktualnej implementacji. Jak nie to out

DATA_FOLDER = "1d_gpw_data"
PERIOD = "1y"
INTERVAL = "1d"


def update_ticker(ticker: str, file_path: str) -> pd.DataFrame:
    print(f"\n=== {ticker} ===")

    def download_full_history() -> pd.DataFrame:
        print("Pobieram pełną historię...")
        df = yf.Ticker(ticker).history(period=PERIOD, interval=INTERVAL)
        df.to_parquet(file_path)
        print("Plik zapisany.")
        return df

    if not os.path.exists(file_path):
        return download_full_history()

    print("Plik istnieje. Sprawdzam aktualność...")
    df_existing = pd.read_parquet(file_path)

    if df_existing.empty:
        return download_full_history()

    last_date = df_existing.index.max()
    print("Ostatnia data:", last_date.date())

    today = datetime.now().date()

    if last_date.date() >= today:
        print("Dane są aktualne.")
        return df_existing

    print("Dane nieaktualne. Aktualizuję...")

    new_data = yf.Ticker(ticker).history(
        start=last_date + timedelta(days=1), interval=INTERVAL
    )

    if not new_data.empty:
        df = pd.concat([df_existing, new_data])
        df = df[~df.index.duplicated(keep="last")]
        df.sort_index(inplace=True)
        df.to_parquet(file_path)
        print("Zaktualizowano.")
        return df
    else:
        print("Brak nowych danych.")
        return df_existing


for file in os.listdir(DATA_FOLDER):
    if file.endswith(".parquet"):
        ticker = file.replace(".parquet", "").replace("_", ".")
        file_path = os.path.join(DATA_FOLDER, file)
        update_ticker(ticker, file_path)

print("\nGotowe. Wszystkie tickery sprawdzone.")
