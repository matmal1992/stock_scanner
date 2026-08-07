from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd


class PriceChart:
    def __init__(self, parquet_file: Path) -> None:
        self.parquet_file = parquet_file
        self.df: pd.DataFrame | None = None

    def load_data(self) -> None:
        if not self.parquet_file.exists():
            raise FileNotFoundError(f"Plik {self.parquet_file} nie istnieje")

        df = pd.read_parquet(self.parquet_file)

        if df.empty:
            raise ValueError("DataFrame jest pusty")

        if "Close" not in df.columns:
            raise ValueError("Brak kolumny 'Close'")

        if isinstance(df.index, pd.DatetimeIndex):
            dt_index = df.index
        else:
            dt_index = pd.to_datetime(df.index)

        if dt_index.tz is not None:
            dt_index = dt_index.tz_localize(None)

        df.index = dt_index
        self.df = df

    def plot(self) -> None:
        if self.df is None:
            raise RuntimeError("Najpierw wywołaj load_data()")

        df = self.df

        print("Dane wczytane poprawnie.")
        print("Liczba wierszy:", len(df))
        print("Zakres dat:", df.index.min(), "->", df.index.max())

        plt.figure()

        plt.plot(
            range(len(df)),
            df["Close"],
        )

        plt.title("Creotech Instruments - Close Price")
        plt.xlabel("Sesja")
        plt.ylabel("Cena zamknięcia")
        plt.grid(True)

        self._configure_x_axis()

        ax = plt.gca()
        ax_any: Any = ax
        ax_any.format_coord = self._format_coord

        plt.tight_layout()
        plt.show()

    def _configure_x_axis(self) -> None:
        if self.df is None:
            return

        step = 20
        index = pd.DatetimeIndex(self.df.index)

        plt.xticks(
            ticks=range(0, len(self.df), step),
            labels=list(index.strftime("%Y-%m-%d"))[::step],
            rotation=45,
        )

    def _format_coord(self, x: float, y: float) -> str:
        if self.df is None:
            return ""

        index = int(round(x))

        if 0 <= index < len(self.df):
            date = self.df.index[index].strftime("%Y-%m-%d")
            return f"Data: {date} | Cena: {y:.2f}"

        return ""
