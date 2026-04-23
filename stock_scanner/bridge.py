from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot

from stock_scanner.scanners.three_tier_scanner import run_3t_strategy


class Worker(QThread):
    def run(self) -> None:
        run_3t_strategy()


class Backend(QObject):
    fileSelected = Signal(str)

    @Slot()
    def run3T(self) -> None:
        self.worker = Worker()
        self.worker.start()

    @Slot(str)
    def loadChart(self, file_url: str) -> None:
        path = file_url.replace("file:///", "")
        filename = Path(path).name

        print("Selected:", path)
        self.fileSelected.emit(filename)
