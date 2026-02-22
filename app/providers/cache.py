from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def cache_path(ticker, interval, period):
    safe = ticker.replace(".", "_")
    return CACHE_DIR / f"{safe}_{interval}_{period}.parquet"


def load_cache(ticker, max_age_minutes=5):
    path = cache_path(ticker, "30m", "5d")

    if not path.exists():
        return None

    file_time = datetime.fromtimestamp(path.stat().st_mtime)

    if datetime.now() - file_time > timedelta(minutes=max_age_minutes):
        return None

    return pd.read_parquet(path)


def save_cache(ticker, df):
    df.to_parquet(cache_path(ticker, "30m", "5d"))
