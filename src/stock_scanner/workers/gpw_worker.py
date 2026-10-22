import logging
import threading
from datetime import datetime

from PySide6.QtCore import QObject, QThread, Signal

from src.stock_scanner.playwright.pap_espi_scraper import PapEspiScraper
from src.stock_scanner.playwright.playwright_session import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class GPWWorker(QThread):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    INTERVAL_SECONDS = 5

    def __init__(self, entry_repo: EntryRepository, worker_status: WorkerStatus) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.entry_scraper: PapEspiScraper | None = None
        self._stop_event = threading.Event()
        self.worker_status = worker_status
        self._last_loop: str = ""

    def run(self) -> None:
        try:
            logger.info("PAP: start wątku %s", threading.current_thread().name)

            self.entry_scraper = PapEspiScraper(PlaywrightSession())
            self.entry_scraper.start()

            logger.info("PAP: przeglądarka uruchomiona")
            self._scrape_and_save()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                self.worker_status.update("GPW", datetime.now().strftime("%H:%M:%S"))
                if self._stop_event.is_set():
                    logger.info("GPW Worker - STOP invoked")
                    break

                self.entry_scraper.refresh_page()
                self._scrape_and_save()

        except Exception as exc:
            logger.exception(f"PAP: błąd podczas inicjalizacji workera: {exc}")

        finally:
            self._cleanup()
            self.finished.emit()

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
                self.log.emit(f"Błąd zapisu: {exc}")

        if new_entries > 0:
            self.log.emit(f"PAP: znaleziono {new_entries} komunikatów")

        self.result.emit(new_entries > 0)

    def _save_entries(self, entries: list[NewsEntry]) -> bool:
        found_new = False

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    # if entry["skipped"] == 0:
                    #     send_telegram_message(entry)
                    # else:
                    #     logger.info(f"GPW: skipped: {entry['title']}")
                    found_new = True

            except Exception as exc:
                self.log.emit(f"PAP: błąd zapisu: {exc}")

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


class GPWService(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()
    stop_requested = Signal()

    def __init__(self, entry_repo: EntryRepository, worker_status: WorkerStatus) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self.worker_status = worker_status
        self._thread: QThread | None = None
        self.worker: GPWWorker | None = None

    def start(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            self.log.emit("Automatyczne pobieranie PAP już działa")
            return False

        self.log.emit("Uruchamiam automatyczne pobieranie PAP")

        self._thread = QThread()
        self.worker = GPWWorker(self.entry_repo, self.worker_status)

        self.worker.moveToThread(self._thread)
        self.stop_requested.connect(self.worker.stop)
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
            self.log.emit("Automatyczne pobieranie PAP nie działa")
            return

        self.log.emit("PAP: zatrzymywanie automatycznego pobierania...")
        self.worker.stop()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _on_worker_result(self, has_new: bool) -> None:
        self.result.emit(has_new)

    def _on_worker_error(self, message: str) -> None:
        self.error.emit(message)

    def _on_worker_finished(self) -> None:
        if self._thread is not None:
            self._thread.quit()

    def _on_thread_finished(self) -> None:
        if self.worker is not None:
            self.worker.deleteLater()

        self._thread = None
        self.worker = None

        self.log.emit("Automatyczne pobieranie PAP zatrzymane")
        self.finished.emit()
