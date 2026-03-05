import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tqdm import tqdm
import pandas as pd
from config import CONFIG_1D as CONFIG
from config import report_path
    
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / CONFIG.data_folder
DATA_DIR.mkdir(exist_ok=True)

log_file = BASE_DIR / CONFIG.failed_tickers_file
log_file.write_text("")
download_report = BASE_DIR / report_path
last_update_path = BASE_DIR / CONFIG.last_update_file

tickers_file = BASE_DIR / CONFIG.tickers_file

# def print_raport(results):
#     print("\n========== RAPORT ==========")
#     print("Zaktualizowano:", len(results["updated"]))
#     print("Pominięto (aktualne):", len(results["skipped"]))
#     print("Krótsza historia:", len(results["short_history"]))
#     print("Delisted / niepoprawne:", len(results["delisted_or_invalid"]))
#     print("Błędy techniczne:", len(results["error"]))
    
def check_last_update():
    today_str = datetime.now().strftime("%Y-%m-%d")
    if last_update_path.exists():
        with open(last_update_path, "r") as f:
            saved_datetime = f.read().strip()
            
        if saved_datetime:
            saved_date = saved_datetime.split(" ")[0]
            
            if saved_date == today_str:
                print("\nDane były już dziś aktualizowane — pomijam pobieranie.\n")
                return True
    return False

# def save_raport_to_file(results):
#     with open(download_report, "w") as f:
#         for key, value in results.items():
#             f.write(f"{key} ({len(value)}):\n")
#             for t in value:
#                 f.write(f"  {t}\n")
#             f.write("\n")
#     pass

# def save_raport_to_file(results):
#     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

#     with open(download_report, "w", encoding="utf-8") as f:
#         f.write("=====================================\n")
#         f.write("          RAPORT POBIERANIA\n")
#         f.write("=====================================\n")
#         f.write(f"Data wygenerowania: {now}\n\n")

#         for key, tickers in results.items():
#             f.write(f"--- {key.upper()} ({len(tickers)}) ---\n")
#             for t in tickers:
#                 f.write(f"{t}\n")
#             f.write("\n")

#     print(f"\nRaport zapisany do: {download_report}")

def update_d1_section(results):

    with open(report_path, "r", encoding="utf-8") as f:
        html = f.read()

    content_html = "<h2>Download 1D Results</h2>"

    for key, tickers in results.items():
        content_html += f"<h3>{key} ({len(tickers)})</h3><ul>"
        for t in tickers:
            content_html += f"<li>{t}</li>"
        content_html += "</ul>"

    html = html.replace(
        "<!-- TU TRAFI RAPORT 1D -->",
        content_html
    )

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

def main():
    
    if check_last_update():
        return
    
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

    start_date = datetime.today() - timedelta(days=CONFIG.period_days)

    for ticker in tqdm(tickers, desc="Pobieranie danych", unit="ticker"):
        with open(log_file, "a") as f:
            f.write(f"{ticker} - nSprawdzanie {ticker}...")

        try:
            t = yf.Ticker(ticker)

            # Próba pobrania 1 roku
            df = t.history(start=start_date, interval=CONFIG.interval)

            if not df.empty:
                filename = ticker.replace(".", "_") + ".parquet"
                filepath = DATA_DIR / filename

                if filepath.exists():
                    try:
                        existing_df = pd.read_parquet(filepath)
                        last_date = existing_df.index.max().date()
                        today = datetime.today().date()
                        if last_date >= today - timedelta(days=1):
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

    # print_raport(results)
    # save_raport_to_file(results)
    update_d1_section(results)
    
    current_datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(last_update_path, "w") as f:
        f.write(current_datetime_str)

if __name__ == "__main__":
    main()
