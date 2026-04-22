from PySide6.QtCore import QObject, QThread, Slot

from stock_scanner.scanners.three_tier_scanner import run_3t_strategy


class Worker(QThread):
    def run(self) -> None:
        run_3t_strategy()


class Backend(QObject):
    @Slot()
    def run3T(self) -> None:
        self.worker = Worker()
        self.worker.start()
