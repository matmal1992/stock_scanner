import os
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

ticker = "CRI.WA"
file_name = "CRI_WA.parquet"


def download_full_history() -> pd.DataFrame:
    print("Pobieram pełną historię...")
    df = yf.Ticker(ticker).history(period="1y", interval="1d")
    df.to_parquet(file_name)
    print("Plik zapisany.")
    return df


if not os.path.exists(file_name):
    df = download_full_history()
else:
    print("Plik istnieje. Sprawdzam aktualność...")

    df_existing = pd.read_parquet(file_name)

    if df_existing.empty:
        df = download_full_history()
    else:
        last_date = df_existing.index.max()
        print("Ostatnia data w pliku:", last_date.date())

        today = datetime.now().date()

        if last_date.date() == today:
            print("Dane są aktualne.")
            df = df_existing
        else:
            print("Dane nieaktualne. Aktualizuję...")
            new_data = yf.Ticker(ticker).history(
                start=last_date + timedelta(days=1), interval="1d"
            )

            if not new_data.empty:
                df = pd.concat([df_existing, new_data])
                df = df[~df.index.duplicated(keep="last")]
                df.sort_index(inplace=True)
                df.to_parquet(file_name)
                print("Plik zaktualizowany.")
            else:
                print("Brak nowych danych.")
                df = df_existing

print("Gotowe.")
