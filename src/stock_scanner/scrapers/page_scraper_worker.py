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

    INTERVAL_MS = 1_000

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.page_content_scraper = PageContentScraper(PlaywrightSession())
        self._timer: QTimer = QTimer(interval=self.INTERVAL_MS)

    def run(self) -> None:
        logger.info("Start workera do scrapowania contentu komunikatu...")

        try:
            self.page_content_scraper.start()
            self._timer.timeout.connect(self._on_timer)
            self._timer.start()
            QThread.currentThread().exec()

        except Exception as exc:
            self.error.emit(f"Page scraper error: {exc}")

        finally:
            self.page_content_scraper.close()
            self.finished.emit()

    def _on_timer(self) -> None:
        entries = self.entry_repo.get_entries_without_content(limit=1)

        if not entries:
            return

        entry = entries[0]

        try:
            self.log.emit("Scraping zawartości komunikatu...")
            content = self.page_content_scraper.scrape_content(entry["link"])
            self.entry_repo.update_content(entry["id"], content)

        except Exception as exc:
            logger.exception("Błąd podczas scrapingu zawartości wpisu")
            self.error.emit(f"Scraper error: {exc}")

    def stop(self) -> None:
        self.log.emit("Zatrzymywanie workera...")

        if self._timer is not None:
            self._timer.stop()

        thread = QThread.currentThread()

        if thread is not None:
            thread.quit()


class ContentScrapeService(QObject):
    result = Signal()
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self._thread: QThread = QThread()
        self.worker: ScraperWorker = ScraperWorker(self.entry_repo)

    def start(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            self.log.emit("Content scrape worker już działa")
            return False

        self.log.emit("Uruchamiam content scrape worker")

        self.worker.moveToThread(self._thread)
        self.worker.result.connect(self._on_worker_result)
        self.worker.error.connect(self._on_worker_error)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self._on_worker_finished)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.started.connect(self.worker.run)
        self._thread.start()

        return True

    def stop(self) -> None:
        if self.worker is None:
            self.log.emit("Content scrape worker nie działa")
            return

        self.log.emit("Content scrape worker został zatrzymany")
        self.worker.stop()

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
        if self.worker is not None:
            self.worker.deleteLater()

        self.log.emit("Content scraping zatrzymane")
        self.finished.emit()
