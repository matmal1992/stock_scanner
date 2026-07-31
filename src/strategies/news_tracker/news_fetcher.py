from PySide6.QtCore import QObject, Signal

from src.strategies.news_tracker.entry_repo import EntryRepository
from src.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.ui.workers.espi_worker import ESPIService


class NewsFetcher(QObject):
    data_ready = Signal(list, bool)
    log = Signal(str)
    error = Signal(str)

    def __init__(self, entry_repo: EntryRepository, tracked_repo: TrackedTickerRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.tracked_repo = tracked_repo
        self.bankier_espi_worker = ESPIService(entry_repo)
        self.bankier_espi_worker.result.connect(self._on_result)
        self.bankier_espi_worker.error.connect(self._on_error)
        self.bankier_espi_worker.log.connect(self._on_log)

    def fetch(self) -> None:
        self.bankier_espi_worker.run()

    def _on_result(self, items: list, has_new_entries: bool) -> None:
        self.data_ready.emit(items, has_new_entries)

    def _on_error(self, message: str) -> None:
        self.error.emit(message)

    def _on_log(self, message: str) -> None:
        self.log.emit(message)
