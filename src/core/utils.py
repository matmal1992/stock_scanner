import io
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def read_parquet(path: Path) -> pd.DataFrame | None:
    try:
        return pd.read_parquet(path)
    except Exception as e:
        print(f"Error reading {path.stem}: {e}")
        return None


def save_tickers(tickers: list[str], path: Path) -> None:
    if not tickers:
        print("Brak tickerów do zapisania")
        return

    try:
        content = ",".join(tickers)

        with open(path, "w") as f:
            f.write(content)

    except Exception as e:
        print(f"Błąd zapisu tickerów do {path}: {e}")


def load_tickers(txt_path: Path) -> list[str]:
    tickers: list[str] = []

    with open(txt_path, "r") as f:
        for line in f:
            parts = line.strip().split(",")

            for p in parts:
                t = p.strip()
                if t:
                    tickers.append(t)

    return tickers


def format_timestamp(ts: int | None) -> str:
    if not ts:
        return ""
    try:
        ts = int(ts)
    except (ValueError, TypeError):
        return ""

    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%d %b %H:%M:%S")


def date_str_to_int(date_str: str) -> int | None:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        return int(dt.timestamp())
    except Exception:
        return None


class EmittingStream(io.TextIOBase):
    def __init__(self, signal: Any) -> None:
        super().__init__()
        self.signal = signal

    def write(self, text: str) -> int:
        if text.strip():
            self.signal.emit(text)
        return len(text)

    def flush(self) -> None:
        pass
