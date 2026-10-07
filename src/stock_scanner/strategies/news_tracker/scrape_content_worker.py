import logging

from PySide6.QtCore import QMutex, QObject, QThread, QWaitCondition, Signal

from src.stock_scanner.core.gemini_prompter import GeminiPrompter
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry

logger = logging.getLogger(__name__)

class ContentWorker(QObject):
    result = Signal(NewsEntry)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self.session = PlaywrightSession()
        self.content_scraper = PageContentScraper(
            self.entry_repo,
            self.session,
        )

        self._running = True
        self._timer = None

    def run(self):
       
        QThread.currentThread().exec()

    def stop(self):
        self._running = False
        
class ContentService(QObject):
        result = Signal(str)
        error = Signal(str)
        log = Signal(str)
        finished = Signal()

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.thread = QThread()
        self.worker = ContentWorker(entry_repo)

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)

        self.worker.result.connect(self.result)
        self.worker.error.connect(self.error)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.finished)

        self.thread.start()

    def stop(self):
        self.worker.stop()

    def wake(self):
        self.worker.wake()