import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PySide6.QtCore import QObject, QThread, QUrl, Signal, Slot

from stock_scanner.scanners.three_tier_scanner import run_3t_strategy


class Worker(QThread):
    def run(self) -> None:
        run_3t_strategy()


class Backend(QObject):
    fileSelected = Signal(str)
    imageReady = Signal(str)

    @Slot()
    def run3T(self) -> None:
        self.worker = Worker()
        self.worker.start()

    @Slot(str)
    def loadChart(self, file_url: str) -> None:
        path = QUrl(file_url).toLocalFile()
        if not path:
            print("Invalid file URL")
            return

        df = pd.read_parquet(path)
        if df.empty:
            print("Loaded parquet file is empty")
            return

        if "Close" not in df.columns:
            print("Missing Close column")
            return

        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
        ax.plot(df.index, df["Close"], color="#00ff99", linewidth=1.8)
        ax.set_title(Path(path).stem)
        ax.set_xlabel("Date")
        ax.set_ylabel("Close")
        ax.grid(True, color="#444444", linestyle="--", linewidth=0.5)
        fig.autofmt_xdate(rotation=45)
        fig.patch.set_facecolor("#121212")
        ax.set_facecolor("#121212")
        ax.tick_params(colors="white", labelcolor="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
            image_path = tmp_file.name

        fig.savefig(image_path, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)

        self.imageReady.emit(QUrl.fromLocalFile(image_path).toString())
