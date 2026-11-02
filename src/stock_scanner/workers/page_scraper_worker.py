import logging

from src.stock_scanner.playwright.pap_entry_scraper import PAPEntryContentScraper
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.base_worker import BaseWorker
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class ScraperWorker(BaseWorker):
    INTERVAL_SECONDS = 1

    def __init__(self, entry_repo: EntryRepository) -> None:
        self._session = PAPEntryContentScraper()
        self.entry_repo = entry_repo
        super().__init__(self._session, "GPW entry scraper")

    def run(self) -> None:
        logger.info("GPW entry scraper worker started")

        try:
            self._session.start()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                WorkerStatus.update("GPW entry scraper", "Loop")
                entries = self.entry_repo.get_entries_without_content(limit=1)

                if not entries:
                    continue

                entry = entries[0]
                content = self._session.scrape_content(entry["link"])
                self.entry_repo.update_content(entry["id"], content)
                WorkerStatus.update("GPW entry scraper", "Last scrape")

        except Exception as exc:
            logger.exception(f"GPW entry scraper exception: {exc}")

        finally:
            logger.info("Closing GPW entry scraper session...")
            self._session.close()
