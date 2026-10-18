import logging
import threading

from PySide6.QtCore import QObject, QThread, Signal

from src.stock_scanner.scrapers.page_content_scraper import PageContentScraper
from src.stock_scanner.scrapers.playwright import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository

logger = logging.getLogger(__name__)


class ScraperWorker(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    INTERVAL_SECONDS = 1

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.page_content_scraper = PageContentScraper(PlaywrightSession())
        self._stop_event = threading.Event()

    def run(self) -> None:
        try:
            logger.info("Start workera do scrapowania contentu komunikatu...")
            self.page_content_scraper.start()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                logger.info("Scraper Worker - 1s")
                if self._stop_event.is_set():
                    break

                entries = self.entry_repo.get_entries_without_content(limit=1)

                if not entries:
                    continue

                entry = entries[0]
                logger.info(f"entry: {entry}")

                content = self.page_content_scraper.scrape_content(entry["link"])
                logger.debug(f"HTML: {content}")
                self.entry_repo.update_content(entry["id"], content)

        except Exception as exc:
            logger.exception(f"Content scraper exception: {exc}")
            self._finish()

    def stop(self) -> None:
        self.log.emit("Zatrzymywanie workera...")
        self._finish()

    def _finish(self) -> None:
        try:
            self.page_content_scraper.close()
        except Exception:
            logger.exception("Błąd podczas zamykania scrapera")

        self.finished.emit()


class ContentScrapeService(QObject):
    result = Signal()
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self._thread: QThread | None = None
        self.worker: ScraperWorker | None = None

    def start(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            self.log.emit("Content scrape worker już działa")
            return False

        self.log.emit("Uruchamiam content scrape worker")
        self._thread = QThread()

        self.worker = ScraperWorker(self.entry_repo)
        self.worker.moveToThread(self._thread)
        self.worker.log.connect(self.log)
        self.worker.error.connect(self._on_worker_error)
        self.worker.result.connect(self._on_worker_result)
        self.worker.finished.connect(self._on_worker_finished)

        self._thread.started.connect(self.worker.run)
        self._thread.finished.connect(self.worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()

        return True

    def stop(self) -> None:
        if self.worker is None or not self.is_running():
            return

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _on_worker_result(self) -> None:
        self.result.emit("Content scraping successful")

    def _on_worker_error(self, message: str) -> None:
        self.error.emit(message)

    def _on_worker_finished(self) -> None:
        if self._thread is not None:
            self._thread.quit()

    def _on_thread_finished(self) -> None:
        self.worker = None
        self._thread = None
        self.finished.emit()
