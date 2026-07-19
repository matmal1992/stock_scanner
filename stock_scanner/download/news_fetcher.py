from typing import Optional

from PySide6.QtCore import QObject, QUrl, Signal

from stock_scanner.download.database import EntryRepository, TrackedTickerRepository
from stock_scanner.ui.workers.google_news_worker import GoogleNewsWorker
from stock_scanner.ui.workers.rss_feed_worker import RSSWorker


class NewsFetcher(QObject):
    data_ready = Signal(list, bool)
    log = Signal(str)
    error = Signal(str)

    def __init__(self, entry_repo: EntryRepository, tracked_repo: TrackedTickerRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.tracked_repo = tracked_repo
        self.bankier_stock_worker = RSSWorker(entry_repo)
        self.bankier_espi_worker = RSSWorker(entry_repo)
        self.google_worker: Optional[GoogleNewsWorker] = None

    def fetch(self) -> None:
        self._connect_worker(self.bankier_stock_worker, "rss_worker")
        self._connect_worker(self.bankier_espi_worker, "rss_worker")

        # self.google_worker = GoogleNewsWorker(self.entry_repo, self.tracked_repo)
        # self._connect_worker(self.google_worker, "google_worker")
        # self.google_worker.run()

        self.bankier_stock_worker.run(QUrl("https://www.bankier.pl/rss/gielda.xml"))
        self.bankier_espi_worker.run(QUrl("https://www.bankier.pl/rss/espi.xml"))

    def _connect_worker(self, worker: RSSWorker | GoogleNewsWorker, attr_name: str) -> None:
        worker.log.connect(self.log)
        worker.error.connect(self.error)
        worker.data_ready.connect(self.data_ready)
        worker.finished.connect(lambda: setattr(self, attr_name, None))
