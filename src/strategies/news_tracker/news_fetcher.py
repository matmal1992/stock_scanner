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

    def fetch(self) -> None:
        # self._connect_worker(self.bankier_espi_worker, "espi_worker")
        self.bankier_espi_worker.run()

        # self.bankier_stock_worker.run(QUrl("https://www.bankier.pl/rss/gielda.xml"))
        # self.bankier_espi_worker.run(QUrl("https://www.bankier.pl/rss/espi.xml"))

    # def _connect_worker(self, worker: ESPIService, attr_name: str) -> None:
    #     worker.log.connect(self.log)
    #     worker.error.connect(self.error)
    #     worker.data_ready.connect(self.data_ready)
    #     worker.finished.connect(lambda: setattr(self, attr_name, None))
