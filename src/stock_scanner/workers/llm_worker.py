import logging
import threading

from PySide6.QtCore import QThread

from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.strategies.news_tracker.gemini_prompter import GeminiPrompter
from src.stock_scanner.workers.telegram import TelegramBot
from src.stock_scanner.workers.worker_manager import ServiceManager
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class LLMWorker(QThread):
    INTERVAL_SECONDS = 1

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.prompter = GeminiPrompter()
        self._stop_event = threading.Event()

    def run(self) -> None:
        logger.info("LLM worker started")

        try:
            self.prompter.start()
        except Exception:
            logger.exception("LLM: błąd uruchamiania promptera")
            return

        while not self._stop_event.wait(self.INTERVAL_SECONDS):
            total_pending = self.entry_repo.get_pending_number()
            WorkerStatus.update("LLM", "Loop")
            WorkerStatus.update("LLM", "Pending", str(total_pending))

            try:
                pending = self.entry_repo.get_pending_with_content(limit=1)

                if not pending:
                    continue

                entry = pending[0]
                response = self.prompter.process_entry(entry)
                if response is None:
                    self.prompter.refresh()
                    continue

                self.entry_repo.update_llm(entry["id"], response)

                entry["llm"] = response["forecast"]
                entry["justification"] = response["justification"]

                TelegramBot.send_alert(entry)
                WorkerStatus.update("LLM", "Last processed")
                self.prompter.refresh()

            except Exception as exc:
                logger.exception("LLM exception: %s", exc)
                try:
                    self.prompter.refresh()
                except Exception:
                    logger.exception("Nie udało się odświeżyć LLM po błędzie")
                continue

    def stop(self) -> None:
        logger.info("Zatrzymywanie LLM workera...")
        self.prompter.close()
        self._stop_event.set()


class LLMService:
    _worker: LLMWorker | None = None

    @classmethod
    def init(cls, entry_repo: EntryRepository) -> None:
        cls.close_worker()
        cls._worker = LLMWorker(entry_repo)
        cls._worker.start()
        ServiceManager.register(cls.close_worker)

    @classmethod
    def close_worker(cls) -> None:
        if getattr(cls, "_worker", None) is not None:
            if cls._worker is not None and cls._worker.isRunning():
                cls._worker.stop()
                cls._worker.wait()

            cls._worker = None
            logger.info("LLM worker closed")
