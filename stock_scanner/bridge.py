import pandas as pd
from PySide6.QtCore import QObject, QThread, QUrl, Signal, Slot

from stock_scanner.scanners.three_tier_scanner import run_3t_strategy


class Worker(QThread):
    def run(self) -> None:
        run_3t_strategy()


class Backend(QObject):
    fileSelected = Signal(str)
    candlesReady = Signal(list)

    @Slot()
    def run3T(self) -> None:
        self.worker = Worker()
        self.worker.start()

    @Slot(str)
    def loadChart(self, file_url: str) -> None:
        path = QUrl(file_url).toLocalFile()
        # filename = Path(path).name

        df = pd.read_parquet(path)

        required = {"Open", "High", "Low", "Close"}
        if not required.issubset(df.columns):
            print("Missing OHLC columns")
            return

        data = []

        for i, row in enumerate(df.itertuples()):
            data.append(
                {
                    "x": i,
                    "open": float(row.Open),
                    "high": float(row.High),
                    "low": float(row.Low),
                    "close": float(row.Close),
                }
            )

        self.candlesReady.emit(data)
