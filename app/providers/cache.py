from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)


def cache_path(ticker):
    return CACHE_DIR / f"{ticker}.parquet"


def load_cache(ticker, max_age_minutes=5):
    path = cache_path(ticker)

    if not path.exists():
        return None

    df = pd.read_parquet(path)

    last_ts = df.index[-1].to_pydatetime()

    if datetime.now() - last_ts > timedelta(minutes=max_age_minutes):
        return None

    return df


def save_cache(ticker, df):
    df.to_parquet(cache_path(ticker))
