import logging
import threading

from PySide6.QtCore import QThread

from src.stock_scanner.playwright.pap_entry_scraper import PAPEntryContentScraper
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.worker_manager import ServiceManager
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class ScraperWorker(QThread):
    INTERVAL_SECONDS = 1

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self._session = PAPEntryContentScraper()
        self._stop_event = threading.Event()

    def run(self) -> None:
        try:
            logger.info("Start workera do scrapowania contentu komunikatu...")
            self._session.start()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                WorkerStatus.update("GPW entry scraper", "Loop")
                entries = self.entry_repo.get_entries_without_content(limit=1)

                if not entries:
                    continue

                entry = entries[0]
                content = self._session.scrape_content(entry["link"])
                self.entry_repo.update_content(entry["id"], content)
                WorkerStatus.update("GPW entry scraper", "Last scrape")

        except Exception as exc:
            logger.exception(f"Content scraper exception: {exc}")

    def stop(self) -> None:
        self._session.close()
        self._stop_event.set()


class ContentScrapeService:
    _worker: ScraperWorker | None = None

    @classmethod
    def init(cls, entry_repo: EntryRepository) -> None:
        cls.close_worker()
        cls._worker = ScraperWorker(entry_repo)
        cls._worker.start()
        ServiceManager.register(cls.close_worker)

    @classmethod
    def close_worker(cls) -> None:
        if cls._worker is not None:
            if cls._worker.isRunning():
                cls._worker.stop()
                cls._worker.wait()

            cls._worker.deleteLater()
            cls._worker = None
            logger.info("Entry scraper worker closed")
        else:
            logger.info("Closing Entry scraper worker - worker already closed")
