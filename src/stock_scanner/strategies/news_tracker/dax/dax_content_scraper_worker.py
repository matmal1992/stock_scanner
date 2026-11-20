import logging

from src.stock_scanner.strategies.news_tracker.dax.dax_entry_scraper import DAXEntryContentScraper
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.base_worker import BaseWorker
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class DaxSingleEntryScraperWorker(BaseWorker):
    INTERVAL_SECONDS = 1

    def __init__(self, entry_repo: EntryRepository) -> None:
        self._session = DAXEntryContentScraper()
        self.entry_repo = entry_repo
        super().__init__(self._session, "DAX entry scraper")

    def run(self) -> None:
        logger.info("DAX entry scraper worker started")

        try:
            self._session.start()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                try:
                    WorkerStatus.update("DAX entry scraper", "Loop")
                    entries = self.entry_repo.get_entries_without_content("DAX", limit=1)

                    if not entries:
                        continue

                    entry = entries[0]
                    content = self._session.scrape_content(entry["link"])
                    self.entry_repo.update_content(entry["id"], content)
                    WorkerStatus.update("DAX entry scraper", "Last scrape")
                    print("dax scraped")
                except Exception as exc:
                    logger.exception(f"DAX entry scraper while loop exception: {exc}")
                    self._session.refresh()
                    continue

        except Exception as exc:
            logger.exception(f"DAX entry scraper exception: {exc}")
            self._session.refresh()

        finally:
            logger.info("Closing DAX entry scraper session...")
            self._session.close()
