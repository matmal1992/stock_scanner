import yfinance as yf
import os
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
from tqdm import tqdm
import pandas as pd

def main():
    INTERVAL = "1d"
    DATA_FOLDER = "1d_gpw_data_test"
    XTB_TICKERS_FILE = "tickers_xtb_WA_test.txt"
    FAILED_TICKERS_FILE = "failed_tickers.txt"
    DOWN_RAPORT = "download_report.txt"
    
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / DATA_FOLDER
    DATA_DIR.mkdir(exist_ok=True)

    log_file = BASE_DIR / FAILED_TICKERS_FILE
    log_file.write_text("")
    download_report = BASE_DIR / DOWN_RAPORT

    tickers_file = BASE_DIR / XTB_TICKERS_FILE

    if not tickers_file.exists():
        print("Brak pliku {XTB_TICKERS_FILE}")
        return

    with open(tickers_file, "r") as f:
        tickers = [t.strip() for t in f.read().split(",") if t.strip()]

    results = {
        "updated": [],
        "skipped": [],
        "short_history": [],
        "delisted_or_invalid": [],
        "error": []
    }

    start_date = datetime.today() - timedelta(days=365)

    for ticker in tqdm(tickers, desc="Pobieranie danych", unit="ticker"):
        with open(log_file, "a") as f:
            f.write(f"{ticker} - nSprawdzanie {ticker}...")

        try:
            t = yf.Ticker(ticker)

            # Próba pobrania 1 roku
            df = t.history(start=start_date, interval="1d")

            if not df.empty:
                filename = ticker.replace(".", "_") + ".parquet"
                filepath = DATA_DIR / filename

                if filepath.exists():
                    try:
                        existing_df = pd.read_parquet(filepath)
                        last_date = existing_df.index.max().date()
                        today = datetime.today().date()
                        if last_date == today:
                            results["skipped"].append(ticker)
                            continue
                    except:
                        pass

                df.to_parquet(filepath)
                results["updated"].append(ticker)
                with open(log_file, "a") as f:
                    f.write(f"{ticker} - updated\n")
                continue

            # Jeśli pusto → sprawdzamy MAX
            df_max = t.history(period="max", interval="1d")

            if df_max.empty:
                results["delisted_or_invalid"].append(ticker)
                with open(log_file, "a") as f:
                    f.write(f"{ticker} - delisted_or_invalid\n")
            else:
                results["short_history"].append(ticker)
                with open(log_file, "a") as f:
                    f.write(f"{ticker} - short_history\n")    

        except Exception as e:
            results["error"].append(ticker)
            # print("BŁĄD:", ticker, e)
            with open(log_file, "a") as f:
                f.write(f"{ticker} - Błąd techniczny: {e}\n")    

    print("\n========== RAPORT ==========")
    print("Zaktualizowano:", len(results["updated"]))
    print("Pominięto (aktualne):", len(results["skipped"]))
    print("Krótsza historia:", len(results["short_history"]))
    print("Delisted / niepoprawne:", len(results["delisted_or_invalid"]))
    print("Błędy techniczne:", len(results["error"]))

    # Zapis raportu
    with open(download_report, "w") as f:
        for key, value in results.items():
            f.write(f"{key} ({len(value)}):\n")
            for t in value:
                f.write(f"  {t}\n")
            f.write("\n")
    pass

if __name__ == "__main__":
    main()
