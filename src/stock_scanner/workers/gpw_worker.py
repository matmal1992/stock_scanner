import logging
import threading

from PySide6.QtCore import QThread

from src.stock_scanner.playwright.pap_espi_scraper import PapEspiScraper
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.worker_manager import ServiceManager
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class GPWWorker(QThread):
    INTERVAL_SECONDS = 5

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self._session = PapEspiScraper()
        self._stop_event = threading.Event()

    def run(self) -> None:
        try:
            logger.info("GPW: przeglądarka uruchomiona")
            self._session.start()
            self._scrape_and_save()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                WorkerStatus.update("GPW", "Loop")
                self._session.refresh_page()
                self._scrape_and_save()

        except Exception as exc:
            logger.exception(f"GPW scraper exception: {exc}")

    def _scrape_and_save(self) -> None:
        entries = self._session.scrape_entries()
        new_entries = 0

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    new_entries += 1

            except Exception as exc:
                logger.error(f"GPW: Błąd zapisu: {exc}")

        if new_entries > 0:
            # logger.info(f"GPW: znaleziono {new_entries} komunikatów")
            print(f"GPW: znaleziono {new_entries} komunikatów")

    def stop(self) -> None:
        self._session.close()
        self._stop_event.set()


class GPWService:
    _worker: GPWWorker | None = None

    @classmethod
    def init(cls, entry_repo: EntryRepository) -> None:
        cls.close_worker()
        cls._worker = GPWWorker(entry_repo)
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
            logger.info("GPW worker closed")
        else:
            logger.info("Closing GPW worker - worker already closed")
