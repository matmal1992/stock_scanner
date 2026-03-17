import yfinance as yf
from datetime import datetime, timedelta
from tqdm import tqdm
import pandas as pd
from report.report_updater import update_down_section


def check_last_update(config):
    today_str = datetime.now().strftime("%Y-%m-%d")

    if config.last_update_path.exists():
        with open(config.last_update_path, "r") as f:
            saved_datetime = f.read().strip()

        if saved_datetime:
            saved_date = saved_datetime.split(" ")[0]

            if saved_date == today_str:
                print("\nDane były już dziś aktualizowane — pomijam pobieranie.\n")
                return True
    return False


def load_tickers(path):
    if not path.exists():
        print(f"Brak pliku {path}")
        return []

    with open(path, "r") as f:
        return [t.strip() for t in f.read().split(",") if t.strip()]


def fetch_data(ticker, config):
    t = yf.Ticker(ticker)
    return t.history(period=f"{config.period_days}d", interval=config.interval)


def process_ticker(ticker, config, results):
    try:
        df = fetch_data(ticker, config)

        if not df.empty:
            filename = ticker.replace(".", "_") + ".parquet"
            filepath = config.data_dir / filename

            if filepath.exists():
                try:
                    existing_df = pd.read_parquet(filepath)
                    last_date = existing_df.index.max().date()
                    today = datetime.today().date()

                    if last_date >= today - timedelta(days=1):
                        results["skipped"].append(ticker)
                        return
                except:
                    pass

            df.to_parquet(filepath)
            results["updated"].append(ticker)
            return

        # Jeśli pusto → sprawdzamy MAX
        t = yf.Ticker(ticker)
        df_max = t.history(period="max", interval="1d")

        if df_max.empty:
            results["delisted_or_invalid"].append(ticker)
        else:
            results["short_history"].append(ticker)

    except Exception as e:
        print(f"ERROR {ticker}: {e}")
        results["error"].append(ticker)


def run_download(config, report_tag, report_stage, use_check=True):
    if use_check and check_last_update(config):
        return

    tickers = load_tickers(config.tickers_path)

    results = {
        "updated": [],
        "skipped": [],
        "short_history": [],
        "delisted_or_invalid": [],
        "error": []
    }

    for ticker in tqdm(tickers, desc=f"Pobieranie {config.interval}", unit="ticker"):
        process_ticker(ticker, config, results)

    update_down_section(results, report_tag, report_stage)

    current_datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(config.last_update_path, "w") as f:
        f.write(current_datetime_str)