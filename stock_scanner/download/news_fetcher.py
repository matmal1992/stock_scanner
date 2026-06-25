from PySide6.QtCore import QObject, Signal
from stock_scanner.ui.workers.rss_feed_worker import RSSWorker
from stock_scanner.ui.workers.google_news_worker import GoogleNewsWorker

class NewsFetcher(QObject):
    data_ready = Signal(list, bool)
    log = Signal(str)
    error = Signal(str)

    def __init__(self):
        super().__init__()
        self.rss_worker = None
        self.google_worker = None

    def fetch(self):
        if self.rss_worker or self.google_worker:
            return

        self.rss_worker = RSSWorker()
        self._connect_worker(self.rss_worker, "rss_worker")

        self.google_worker = GoogleNewsWorker()
        self._connect_worker(self.google_worker, "google_worker")

        self.rss_worker.run()
        self.google_worker.run()

    def _connect_worker(self, worker, attr_name):
        worker.log.connect(self.log)
        worker.error.connect(self.error)
        worker.data_ready.connect(self.data_ready)
        worker.finished.connect(lambda: setattr(self, attr_name, None))