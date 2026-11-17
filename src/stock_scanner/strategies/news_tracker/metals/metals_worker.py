import logging

# from src.stock_scanner.playwright.pap_espi_scraper import PapEspiScraper
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.base_worker import BaseWorker
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)

# GOLD:
# https://wire.quants.space/?asset=commodity-gcusd%2Cfx-dx-y.nyb&area=macro&tag=inflation%2Crate+decision%2Ccentral+bank+talk%2Cjobs%2Cgrowth+data%2Cbond+auction%2Csanctions

# SILVER:
#  dorzucić silver do golda

# strona do wykorzystania
# https://www.financialjuice.com/home


class LSEWorker(BaseWorker):
    INTERVAL_SECONDS = 5

    def __init__(self, entry_repo: EntryRepository) -> None:
        # self._session = PapEspiScraper()
        self.entry_repo = entry_repo
        super().__init__(self._session, "LSE")

    def run(self) -> None:
        logger.info("LSE worker started")

        try:
            self._session.start()
            # self._scrape_and_save()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                WorkerStatus.update("LSE", "Loop")
                # self._session.refresh_page()
                # self._scrape_and_save()

        except Exception as exc:
            logger.exception(f"LSE exception: {exc}")

        finally:
            logger.info("Closing LSE session...")
            # self._session.close()

    # def _scrape_and_save(self) -> None:
    #     entries = self._session.scrape_entries()
    #     new_entries = 0

    #     for entry in entries:
    #         try:
    #             if self.entry_repo.save(entry):
    #                 new_entries += 1

    #         except Exception as exc:
    #             logger.error(f"LSE: Błąd zapisu: {exc}")

    #     if new_entries > 0:
    #         # logger.info(f"LSE: znaleziono {new_entries} komunikatów")
    #         print(f"LSE: znaleziono {new_entries} komunikatów")

    # def stop(self) -> None:
    #     self._session.close()
    #     self._stop_event.set()
