import logging
import threading

from PySide6.QtCore import QThread

from src.stock_scanner.playwright.pap_entry_scraper import PAPEntryContentScraper
from src.stock_scanner.playwright.playwright_session import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class ScraperWorker(QThread):
    INTERVAL_SECONDS = 1

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.page_content_scraper = PAPEntryContentScraper(PlaywrightSession())
        self._stop_event = threading.Event()

    def run(self) -> None:
        try:
            logger.info("Start workera do scrapowania contentu komunikatu...")
            self.page_content_scraper.start()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                WorkerStatus.update("GPW entry scraper", "Loop")
                if self._stop_event.is_set():
                    logger.info("Content Scraper Worker - STOP invoked")
                    break

                entries = self.entry_repo.get_entries_without_content(limit=1)

                if not entries:
                    continue

                entry = entries[0]
                content = self.page_content_scraper.scrape_content(entry["link"])
                self.entry_repo.update_content(entry["id"], content)
                WorkerStatus.update("GPW entry scraper", "Last scrape")

        except Exception as exc:
            logger.exception(f"Content scraper exception: {exc}")
            self._finish()

    def stop(self) -> None:
        logger.info("Entry scraper - Zatrzymywanie workera...")
        self._finish()

    def _finish(self) -> None:
        try:
            self.page_content_scraper.close()
        except Exception:
            logger.exception("Błąd podczas zamykania scrapera")


class ContentScrapeService:
    _thread: QThread | None
    _worker: ScraperWorker | None

    @classmethod
    def start(cls, entry_repo: EntryRepository) -> None:
        cls._thread = QThread()
        cls._worker = ScraperWorker(entry_repo)
        cls._worker.moveToThread(cls._thread)

        cls._thread.started.connect(cls._worker.run)
        cls._thread.finished.connect(cls._worker.deleteLater)
        cls._thread.finished.connect(cls._thread.deleteLater)
        cls._thread.finished.connect(cls._on_thread_finished)

        cls._thread.start()

    @classmethod
    def stop(cls) -> None:
        thread_running = cls._thread is not None and cls._thread.isRunning()
        if cls._worker is None or not thread_running:
            return

    @classmethod
    def _on_thread_finished(cls) -> None:
        cls._thread = None
        cls._worker = None
