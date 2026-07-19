from typing import Optional

from PySide6.QtCore import QObject, Signal

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
        self.rss_worker: Optional[RSSWorker] = None
        self.google_worker: Optional[GoogleNewsWorker] = None

    def fetch(self) -> None:
        if self.rss_worker or self.google_worker:
            return

        self.rss_worker = RSSWorker(self.entry_repo)
        self._connect_worker(self.rss_worker, "rss_worker")

        self.google_worker = GoogleNewsWorker(self.entry_repo, self.tracked_repo)
        self._connect_worker(self.google_worker, "google_worker")

        self.rss_worker.run()
        # self.google_worker.run()

    def _connect_worker(self, worker: RSSWorker | GoogleNewsWorker, attr_name: str) -> None:
        worker.log.connect(self.log)
        worker.error.connect(self.error)
        worker.data_ready.connect(self.data_ready)
        worker.finished.connect(lambda: setattr(self, attr_name, None))
