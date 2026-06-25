import io
from datetime import datetime
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Signal


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


class EmittingStream(io.TextIOBase):
    def __init__(self, signal: Signal) -> None:
        super().__init__()
        self.signal = signal

    def write(self, text: str) -> int:
        if text.strip():
            self.signal.emit(text)
        return len(text)

    def flush(self) -> None:
        pass


class NewsFormatter:
    @staticmethod
    def format(items):
        lines = []
        links = []

        for title, link, published, source_type in items:
            prefix = f"[{source_type.upper()}]"
            links.append(link)

            if published:
                dt = datetime.fromtimestamp(published)
                time_str = dt.strftime("%d %b %H:%M")
                lines.append(f"{time_str} {prefix} {title}")
            else:
                lines.append(f"{prefix} {title}")

        return lines, links