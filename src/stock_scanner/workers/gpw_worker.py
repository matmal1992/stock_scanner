import logging
import threading

from PySide6.QtCore import QThread

from src.stock_scanner.playwright.pap_espi_scraper import PapEspiScraper
from src.stock_scanner.playwright.playwright_session import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class GPWWorker(QThread):
    INTERVAL_SECONDS = 5

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.entry_scraper: PapEspiScraper | None = None
        self._stop_event = threading.Event()
        self._last_loop: str = ""

    def run(self) -> None:
        try:
            self.entry_scraper = PapEspiScraper(PlaywrightSession())
            self.entry_scraper.start()

            logger.info("GPW: przeglądarka uruchomiona")
            self._scrape_and_save()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                WorkerStatus.update("GPW", "Loop")
                if self._stop_event.is_set():
                    logger.info("GPW Worker - STOP invoked")
                    break

                self.entry_scraper.refresh_page()
                self._scrape_and_save()

        except Exception as exc:
            logger.exception(f"GPW: błąd podczas inicjalizacji workera: {exc}")

        finally:
            self._cleanup()

    def _scrape_and_save(self) -> None:
        if self.entry_scraper is None:
            return

        entries = self.entry_scraper.scrape_entries()
        new_entries = 0

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    new_entries += 1

            except Exception as exc:
                logger.error(f"GPW: Błąd zapisu: {exc}")

        if new_entries > 0:
            logger.info(f"GPW: znaleziono {new_entries} komunikatów")

    def _save_entries(self, entries: list[NewsEntry]) -> bool:
        found_new = False

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    found_new = True

            except Exception as exc:
                logger.error(f"GPW: błąd zapisu: {exc}")

        return found_new

    def stop(self) -> None:
        self._stop_event.set()

    def _cleanup(self) -> None:
        if self.entry_scraper is not None:
            try:
                self.entry_scraper.close()
            except Exception:
                logger.exception("PAP: błąd zamykania Playwright")
            finally:
                self.entry_scraper = None


class GPWService:
    _thread: QThread | None
    _worker: GPWWorker | None

    @classmethod
    def start(cls, entry_repo: EntryRepository) -> None:
        cls._thread = QThread()
        cls._worker = GPWWorker(entry_repo)
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
