import logging
from typing import Callable

from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.gpw_worker import GPWWorker
from src.stock_scanner.workers.llm_worker import LLMWorker
from src.stock_scanner.workers.page_scraper_worker import ScraperWorker
from src.stock_scanner.workers.telegram import TelegramBot
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class ServiceManager:
    _services: list[Callable[[], None]] = []
    _gpw_worker: GPWWorker
    _llm_worker: LLMWorker
    _scraper_worker: ScraperWorker

    @classmethod
    def init_all(cls, entry_repo: EntryRepository) -> None:
        WorkerStatus.init()
        TelegramBot.init(entry_repo)
        cls._gpw_worker = GPWWorker(entry_repo)
        cls._gpw_worker.start()
        cls._llm_worker = LLMWorker(entry_repo)
        cls._llm_worker.start()
        cls._scraper_worker = ScraperWorker(entry_repo)
        cls._scraper_worker.start()

    @classmethod
    def register(cls, service_stop_callback: Callable[[], None]) -> None:
        cls._services.append(service_stop_callback)

    @classmethod
    def close_all(cls) -> None:
        for stop_func in cls._services:
            # try:
            stop_func()
        # except Exception as e:
        # logger.exception(f"Błąd podczas zamykania serwisu: {e}")
        cls._services.clear()
        logger.info("Wszystkie zarejestrowane workery zostały zamknięte.")
