import logging
import threading
from typing import Any

from PySide6.QtCore import QThread

from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.workers.worker_manager import ServiceManager

logger = logging.getLogger(__name__)


class BaseWorker(QThread):
    _worker: Any | None = None
    _stop_event = threading.Event()

    def __init__(self, entry_repo: EntryRepository, session: Any) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self._session = session
        type(self).close_worker()
        type(self)._worker = self
        ServiceManager.register(type(self).close_worker)

    def stop(self) -> None:
        if self._session and hasattr(self._session, "close"):
            self._session.close()
        self._stop_event.set()

    @classmethod
    def close_worker(cls) -> None:
        if cls._worker is not None:
            if cls._worker.isRunning():
                cls._worker.stop()
                cls._worker.wait()

            cls._worker.deleteLater()
            cls._worker = None
            logger.info("LLM worker closed")
        else:
            logger.info("Closing LLM worker - worker already closed")
