import logging
from typing import Callable

from src.stock_scanner.strategies.news_tracker.dax.dax_entry_worker import DaxEntryWorker
from src.stock_scanner.strategies.news_tracker.dax.dax_list_worker import DAXListWorker
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.strategies.news_tracker.gpw.gpw_entry_worker import GPWEntryWorker
from src.stock_scanner.strategies.news_tracker.gpw.gpw_list_worker import GPWListWorker
from src.stock_scanner.strategies.news_tracker.llm.llm_worker import LLMWorker
from src.stock_scanner.workers.telegram import TelegramBot
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class ServiceManager:
    _services: list[Callable[[], None]] = []
    _gpw_list_worker: GPWListWorker
    _dax_list_worker: DAXListWorker
    _dax_entry_worker: DaxEntryWorker
    _llm_worker: LLMWorker
    _gpw_entry_worker: GPWEntryWorker

    @classmethod
    def init_all(cls, entry_repo: EntryRepository) -> None:
        WorkerStatus.init()
        TelegramBot.init(entry_repo)
        # cls._gpw_list_worker = GPWListWorker(entry_repo)
        # cls._gpw_list_worker.start()
        # cls._gpw_entry_worker = GPWEntryWorker(entry_repo)
        # cls._gpw_entry_worker.start()
        cls._dax_list_worker = DAXListWorker(entry_repo)
        cls._dax_list_worker.start()
        cls._dax_entry_worker = DaxEntryWorker(entry_repo)
        cls._dax_entry_worker.start()
        cls._llm_worker = LLMWorker(entry_repo)
        cls._llm_worker.start()

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
