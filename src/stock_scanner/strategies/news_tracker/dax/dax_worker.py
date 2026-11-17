import logging

from src.stock_scanner.strategies.news_tracker.dax.dax_scraper import DaxScraper
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.base_worker import BaseWorker
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class DAXWorker(BaseWorker):
    INTERVAL_SECONDS = 5

    def __init__(self, entry_repo: EntryRepository) -> None:
        self._session = DaxScraper()
        self.entry_repo = entry_repo
        super().__init__(self._session, "DAX")

    def run(self) -> None:
        logger.info("DAX worker started")

        try:
            self._session.start()
            self._scrape_and_save()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                try:
                    WorkerStatus.update("DAX", "Loop")
                    self._scrape_and_save()
                except Exception as exc:
                    self._handle_error("DAX while loop exception", str(exc))
                    continue

        except Exception as exc:
            self._handle_error("DAX main exception", str(exc))

        finally:
            logger.info("Closing DAX session...")
            self._session.close()

    def _scrape_and_save(self) -> None:
        entries = self._session.scrape_entries()

        for entry in entries:
            try:
                self.entry_repo.save(entry)
            except Exception as exc:
                logger.error(f"DAX: Błąd zapisu: {exc}")

    def stop(self) -> None:
        self._session.close()
        self._stop_event.set()

    def _handle_error(self, message: str, full_log: str) -> None:
        screenshot = self._session.session.page.screenshot(full_page=True)
        WorkerStatus.update("DAX", "Last error")
        WorkerStatus.update_error_status(message, full_log, screenshot)
        logger.error(message + "\n" + full_log)
        self._session.refresh_page()
