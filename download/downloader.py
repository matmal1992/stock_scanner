import yfinance as yf
from datetime import datetime, timedelta, timezone
from tqdm import tqdm
import pandas as pd
from report.report_updater import update_down_section


def check_last_update(config, interval_minutes=None):
    if not config.last_update_path.exists():
        return False

    try:
        with open(config.last_update_path, "r") as f:
            saved_datetime_str = f.read().strip()

        if not saved_datetime_str:
            return False

        saved_datetime = datetime.strptime(saved_datetime_str, "%Y-%m-%d %H:%M:%S")

        now = datetime.now()
        diff = now - saved_datetime

        if interval_minutes is None:
            if saved_datetime.date() == now.date():
                print("\nDane D1 były już dziś aktualizowane — pomijam.\n")
                return True

        else:
            diff_minutes = diff.total_seconds() / 60

            print(f"[DEBUG] Ostatnia aktualizacja: {saved_datetime}")
            print(f"[DEBUG] Minuty od ostatniego run: {diff_minutes:.2f}")

            if diff_minutes < interval_minutes:
                print(f"\nPomijam — ostatni run {diff_minutes:.2f} min temu (< {interval_minutes})\n")
                return True

    except Exception as e:
        print(f"Błąd przy check_last_update: {e}")

    return False


# def should_skip_ticker(filepath, interval_minutes):
#     if not filepath.exists():
#         return False

#     try:
#         df = pd.read_parquet(filepath)

#         if df.empty:
#             return False

#         last_timestamp = df.index.max()
#         now = datetime.now(timezone.utc)

#         if now - last_timestamp < timedelta(minutes=interval_minutes):
#             return True

#     except Exception as e:
#         print(f"Błąd przy sprawdzaniu {filepath}: {e}")

#     return False
from datetime import datetime, timezone, timedelta
import pandas as pd

def should_skip_ticker(filepath, interval_minutes):
    if not filepath.exists():
        print(f"[DEBUG] Plik nie istnieje: {filepath}")
        return False

    try:
        df = pd.read_parquet(filepath)

        if df.empty:
            print(f"[DEBUG] Plik pusty: {filepath}")
            return False

        # Upewniamy się, że indeks jest DatetimeIndex z UTC
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)
        elif df.index.tz is None:
            df.index = df.index.tz_localize('UTC')

        last_timestamp = df.index.max()
        now = pd.Timestamp.now(tz=last_timestamp.tz)
        diff_minutes = (now - last_timestamp).total_seconds() / 60

        # Debug info
        print(f"[DEBUG] Plik: {filepath}")
        print(f"[DEBUG] Last timestamp: {last_timestamp} (tz: {last_timestamp.tzinfo})")
        print(f"[DEBUG] Now: {now}")
        print(f"[DEBUG] Różnica czasu w minutach: {diff_minutes:.2f}")

        if diff_minutes < interval_minutes:
            print(f"[DEBUG] Pomijam ticker (różnica {diff_minutes:.2f} min < {interval_minutes} min)")
            return True
        else:
            print(f"[DEBUG] Pobieram ticker (różnica {diff_minutes:.2f} min >= {interval_minutes} min)")

    except Exception as e:
        print(f"Błąd przy sprawdzaniu {filepath}: {e}")

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
            filename = f"{ticker}.parquet"
            filepath = config.data_dir / filename

            if filepath.exists():
                try:
                    if config.interval in ["15m", "5m"]:
                        if should_skip_ticker(filepath, config.interval_minutes):
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


def run_download(config, report_tag, report_stage):
    if config.interval in ["1d"]:
        if check_last_update(config):
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