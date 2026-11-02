import logging
import threading
from typing import Any

from PySide6.QtCore import QThread

logger = logging.getLogger(__name__)


class BaseWorker(QThread):
    def __init__(self, session: Any, worker_name: str) -> None:
        super().__init__()
        self._session = session
        self._worker_name = worker_name
        self._stop_event = threading.Event()

        from src.stock_scanner.workers.worker_manager import ServiceManager

        ServiceManager.register(self.close_worker)

    def close_worker(self) -> None:
        self._stop_event.set()
        self.quit()
        self.wait()
        logger.info(f"{self._worker_name} worker closed")
