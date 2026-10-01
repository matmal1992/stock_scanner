import logging
from typing import Optional

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from src.stock_scanner.scrapers.pap_espi import PapEspiScraper
from src.stock_scanner.scrapers.playwright import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry

logger = logging.getLogger(__name__)


class GPWWorker(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    INTERVAL_MS = 5_000

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo

        self.session = PlaywrightSession()
        self.scraper = PapEspiScraper(self.session)
        self._timer: QTimer | None = None

    def run(self) -> None:
        self.log.emit("Start scrapowania komunikatów giełdowych z PAP...")

        try:
            self.scraper.start()
            self._timer = QTimer()
            self._timer.setInterval(self.INTERVAL_MS)
            self._timer.timeout.connect(self._on_timer)
            self._scrape_and_save()
            self._timer.start()
            QThread.currentThread().exec()

        except Exception as exc:
            self.error.emit(f"PAP error: {exc}")

        finally:
            self.scraper.close()
            self.finished.emit()

    def _on_timer(self) -> None:
        try:
            self.log.emit("PAP: czas na kolejne pobieranie")

            self.scraper.refresh()
            self._scrape_and_save()

        except Exception as exc:
            self.error.emit(f"PAP error podczas odświeżania: {exc}")

    def _scrape_and_save(self) -> None:
        entries = self.scraper.scrape()

        self.log.emit(f"PAP: znaleziono {len(entries)} komunikatów")

        has_new = False

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    has_new = True

            except Exception as exc:
                self.log.emit(f"Błąd zapisu: {exc}")

        self.result.emit(has_new)

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
        self.log.emit("PAP: zatrzymywanie workera...")

        if self._timer is not None:
            self._timer.stop()

        thread = QThread.currentThread()

        if thread is not None:
            thread.quit()


class GPWService(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self._thread: Optional[QThread] = None
        self.worker: Optional[GPWWorker] = None

    def start(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            self.log.emit("Automatyczne pobieranie PAP już działa")
            return False

        self.log.emit("Uruchamiam automatyczne pobieranie PAP")

        self._thread = QThread()
        self.worker = GPWWorker(self.entry_repo)

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
