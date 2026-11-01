import logging
from typing import Callable

logger = logging.getLogger(__name__)


class ServiceManager:
    _services: list[Callable[[], None]] = []

    @classmethod
    def register(cls, service_stop_callback: Callable[[], None]) -> None:
        cls._services.append(service_stop_callback)

    @classmethod
    def stop_all(cls) -> None:
        for stop_func in cls._services:
            # try:
            stop_func()
        # except Exception as e:
        # logger.exception(f"Błąd podczas zamykania serwisu: {e}")
        cls._services.clear()
        logger.info("Wszystkie zarejestrowane workery zostały zamknięte.")
