import logging

from src.stock_scanner.playwright.pap_espi_scraper import PapEspiScraper
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.base_worker import BaseWorker
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class GPWWorker(BaseWorker):
    INTERVAL_SECONDS = 5

    def __init__(self, entry_repo: EntryRepository) -> None:
        self._session = PapEspiScraper()
        self.entry_repo = entry_repo
        super().__init__(self._session, "GPW")

    def run(self) -> None:
        logger.info("GPW worker started")

        try:
            self._session.start()
            self._scrape_and_save()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                WorkerStatus.update("GPW", "Loop")
                self._session.refresh_page()
                self._scrape_and_save()

        except Exception as exc:
            logger.exception(f"GPW exception: {exc}")

        finally:
            logger.info("Closing GPW session...")
            self._session.close()

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
