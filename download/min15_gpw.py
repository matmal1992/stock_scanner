import yfinance as yf
from datetime import datetime, timedelta
from tqdm import tqdm
import pandas as pd
from config import CONFIG_15M as CONFIG
from report.report_updater import update_down_section
    
# def check_last_update():
#     today_str = datetime.now().strftime("%Y-%m-%d")
#     if last_update_path.exists():
#         with open(last_update_path, "r") as f:
#             saved_datetime = f.read().strip()
            
#         if saved_datetime:
#             saved_date = saved_datetime.split(" ")[0]
            
#             if saved_date == today_str:
#                 print("\nDane były już dziś aktualizowane — pomijam pobieranie.\n")
#                 return True
#     return False

def main():
    # if check_last_update():
    #     return
    
    if not CONFIG.tickers_path.exists():
        print("Brak pliku {CONFIG.tickers_path}")
        return

    with open(CONFIG.tickers_path, "r") as f:
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
        try:
            t = yf.Ticker(ticker)

            # Próba pobrania 60 dni
            df = t.history(start=start_date, interval=CONFIG.interval)

            if not df.empty:
                filename = ticker.replace(".", "_") + ".parquet"
                filepath = CONFIG.data_dir / filename

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
                continue

            # Jeśli pusto → sprawdzamy MAX
            df_max = t.history(period="max", interval="1d")

            if df_max.empty:
                results["delisted_or_invalid"].append(ticker)
            else:
                results["short_history"].append(ticker)

        except Exception as e:
            results["error"].append(ticker)
            print("BŁĄD:", ticker, e)

    update_down_section(results, "<!-- T2_DOWNLOAD -->", "second")

    current_datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(CONFIG.last_update_path, "w") as f:
        f.write(current_datetime_str)

if __name__ == "__main__":
    main()
