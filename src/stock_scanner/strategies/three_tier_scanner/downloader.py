from datetime import datetime
from pathlib import Path
from typing import Callable

import pandas as pd
import yfinance as yf

from config.app_config import DownloadConfig
from src.stock_scanner.strategies.three_tier_scanner.report_updater import update_down_section


def is_T1_data_actual(config: DownloadConfig) -> bool:
    if not config.last_update_path.exists():
        return False

    try:
        with open(config.last_update_path, "r") as f:
            saved_datetime_str = f.read().strip()

        if not saved_datetime_str:
            return False

        saved_datetime = datetime.strptime(saved_datetime_str, "%Y-%m-%d %H:%M:%S")
        today = datetime.now().date()

        if saved_datetime.date() == today:
            return True

    except Exception as e:
        print(f"Błąd przy sprawdzaniu T1 update: {e}")

    return False


def should_skip_ticker(filepath: Path, interval_minutes: int) -> bool:
    if not filepath.exists():
        return False

    try:
        df = pd.read_parquet(filepath)

        if df.empty:
            return False

        # Normalizacja indeksu czasu
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)
        elif df.index.tz is None:
            df.index = df.index.tz_localize("UTC")

        last_timestamp = df.index.max()
        now = pd.Timestamp.now(tz=last_timestamp.tz)

        diff_minutes = (now - last_timestamp).total_seconds() / 60

        if diff_minutes < interval_minutes:
            return True
        else:
            return False

    except Exception as e:
        print(f"Błąd przy sprawdzaniu {filepath}: {e}")
        return False


def load_tickers(path: Path) -> list[str]:
    if not path.exists():
        print(f"Brak pliku {path}")
        return []

    with open(path, "r") as f:
        return [t.strip() for t in f.read().split(",") if t.strip()]


def fetch_data(ticker: str, config: DownloadConfig) -> pd.DataFrame:
    t = yf.Ticker(ticker)
    return t.history(period=f"{config.period_days}d", interval=config.interval)


def process_ticker(ticker: str, config: DownloadConfig, results: dict[str, list]) -> None:
    try:
        filepath = config.data_dir / f"{ticker}.parquet"

        # 0. SKIP LOGIC (intraday only)
        if config.interval in ["15m", "5m"]:
            if should_skip_ticker(filepath, config.interval_minutes):
                print(f"SKIPPED {ticker}")
                results["skipped"].append(ticker)
                return

        # 1. CURRENT DATA
        df = fetch_history(ticker, period=f"{config.period_days}d", interval=config.interval)

        # 2. FALLBACK (only for classification, NOT decision)
        df_max = fetch_history(ticker, period="max", interval="1d")

        # 3. SINGLE DECISION POINT
        status = classify_ticker(df, df_max)
        results[status].append(ticker)

        # 4. SAVE ONLY IF VALID
        if status == "updated":
            df.to_parquet(filepath)

    except Exception as e:
        print(f"ERROR {ticker}: {e}")
        results["error"].append(ticker)


def is_valid_df(df: pd.DataFrame) -> bool:
    if df is None or df.empty:
        return False

    if "Close" not in df.columns:
        return False

    if df["Close"].dropna().empty:
        return False

    return True


def classify_ticker(df: pd.DataFrame | None, df_max: pd.DataFrame | None) -> str:
    # brak danych kompletnie
    if df is None or df.empty:
        if df_max is None or df_max.empty:
            return "delisted_or_invalid"
        return "short_history"

    # brak kluczowych kolumn
    if "Close" not in df.columns:
        return "delisted_or_invalid"

    # same NaN / śmieci
    if df["Close"].dropna().empty:
        return "delisted_or_invalid"

    # bardzo mało danych → niepełna historia
    if len(df) < 5:
        return "short_history"

    return "updated"


def fetch_history(ticker: str, period: str, interval: str) -> pd.DataFrame:
    try:
        return yf.Ticker(ticker).history(period=period, interval=interval)
    except Exception:
        return pd.DataFrame()


def run_download(
    config: DownloadConfig,
    report_tag: str,
    report_stage: str,
    progress_callback: Callable[[int], None] | None = None,
) -> None:
    if config.interval == "1d" and is_T1_data_actual(config):
        print("Skip D1 download — already updated today")
        return

    tickers = load_tickers(config.tickers_path)
    total = len(tickers)

    results: dict[str, list[str]] = {
        "updated": [],
        "skipped": [],
        "short_history": [],
        "delisted_or_invalid": [],
        "error": [],
    }

    for i, ticker in enumerate(tickers, start=1):
        process_ticker(ticker, config, results)

        if progress_callback:
            progress_callback(int((i / total) * 100))

    update_down_section(results, report_tag, report_stage)

    with open(config.last_update_path, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
