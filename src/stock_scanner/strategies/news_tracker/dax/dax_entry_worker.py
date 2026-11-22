import logging

from src.stock_scanner.strategies.news_tracker.dax.dax_entry_scraper import DAXEntryScraper
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.base_worker import BaseWorker
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class DaxEntryWorker(BaseWorker):
    INTERVAL_SECONDS = 1

    def __init__(self, entry_repo: EntryRepository) -> None:
        self._session = DAXEntryScraper()
        self.entry_repo = entry_repo
        super().__init__(self._session, "DAX entry scraper")

    def run(self) -> None:
        logger.info("DAX entry scraper worker started")

        try:
            self._session.start()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                try:
                    WorkerStatus.update("DAX", "Entry scraper loop")
                    entries = self.entry_repo.get_entries_without_content("DAX", limit=1)

                    if not entries:
                        continue

                    entry = entries[0]
                    content = self._session.scrape_content(entry["link"])
                    self.entry_repo.update_content(entry["id"], content)
                    WorkerStatus.update("DAX", "Entry scraper - last scrape")
                except Exception as exc:
                    self._handle_error("DAX entry scraper loop exception", str(exc))

        except Exception as exc:
            self._handle_error("DAX entry scraper exception", str(exc))

        finally:
            logger.info("Closing DAX entry scraper session...")
            self._session.close()

    def _handle_error(self, message: str, full_log: str) -> None:
        screenshot = self._session.session.page.screenshot(full_page=True)
        WorkerStatus.update("DAX", "Entry scraper - last error")
        WorkerStatus.update_error_status(message, full_log, screenshot)
        logger.error(message + "\n" + full_log)
        self._session.refresh()
