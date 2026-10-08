import logging

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from src.stock_scanner.scrapers.page_content_scraper import PageContentScraper
from src.stock_scanner.scrapers.playwright import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository

logger = logging.getLogger(__name__)


class ScraperWorker(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()
    stop_requested = Signal()

    INTERVAL_MS = 1_000

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.page_content_scraper = PageContentScraper(PlaywrightSession())
        self._timer: QTimer = QTimer(self, interval=self.INTERVAL_MS)

    def run(self) -> None:
        logger.info("Start workera do scrapowania contentu komunikatu...")

        try:
            self.page_content_scraper.start()
            self._timer.timeout.connect(self._on_timer)
            self._timer.start()
            logger.info("Timer scrapera uruchomiony")

        except Exception as exc:
            logger.exception("Nie udało się uruchomić scrapera")
            self.error.emit(f"Page scraper error: {exc}")
            self._finish()

    def _on_timer(self) -> None:
        logger.info("On timer wywołany")
        try:
            entries = self.entry_repo.get_entries_without_content(limit=1)
        except Exception as exc:
            logger.exception("Błąd podczas pobierania wpisu do scrapowania")
            self.error.emit(f"Scraper repository error: {exc}")
            return

        if not entries:
            return

        entry = entries[0]

        try:
            logger.info("Scraping zawartości komunikatu...")
            content = self.page_content_scraper.scrape_content(entry["link"])
            self.entry_repo.update_content(entry["id"], content)

        except Exception as exc:
            logger.exception("Błąd podczas scrapingu zawartości wpisu")
            self.error.emit(f"Scraper error: {exc}")

    def stop(self) -> None:
        self.log.emit("Zatrzymywanie workera...")
        self._finish()

    def _finish(self) -> None:
        self._timer.stop()

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
        if self.is_running():
            self.log.emit("Content scrape worker już działa")
            return False

        self.log.emit("Uruchamiam content scrape worker")

        self._thread = QThread()
        self.worker = ScraperWorker(self.entry_repo)
        self.worker.moveToThread(self._thread)
        self.worker.stop_requested.connect(self.worker.stop)
        self.worker.result.connect(self._on_worker_result)
        self.worker.error.connect(self._on_worker_error)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self._on_worker_finished)
        self._thread.finished.connect(self.worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.started.connect(self.worker.run)
        self._thread.start()

        return True

    def stop(self) -> None:
        if self.worker is None or not self.is_running():
            self.log.emit("Content scrape worker nie działa")
            return

        self.log.emit("Wysyłam żądanie zatrzymania content scrape workera")
        self.worker.stop_requested.emit()

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
        self.log.emit("Content scraping zatrzymane")
        self.finished.emit()
