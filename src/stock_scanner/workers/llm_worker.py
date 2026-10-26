import logging
import threading

from PySide6.QtCore import QThread

from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.strategies.news_tracker.gemini_prompter import GeminiPrompter
from src.stock_scanner.workers.telegram import TelegramBot
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

            if self._stop_event.is_set():
                logger.info("LLM Worker - STOP invoked")
                break

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

    def _cleanup(self) -> None:
        if self.prompter is not None:
            try:
                self.prompter.close()
            except Exception:
                logger.exception("LLM: błąd zamykania promptera")
            finally:
                self.prompter.close()

    def stop(self) -> None:
        logger.info("Zatrzymywanie LLM workera...")
        self._stop_event.set()
        self._finish()

    def _finish(self) -> None:
        try:
            self.prompter.close()
        except Exception:
            logger.exception("Błąd podczas zamykania LLM promptera")

    def get_screenshot(self) -> bytes:
        return self.prompter._screenshot


class LLMService:
    _thread: QThread | None
    _worker: LLMWorker | None

    @classmethod
    def start(cls, entry_repo: EntryRepository) -> None:
        cls._thread = QThread()
        cls._worker = LLMWorker(entry_repo)
        cls._worker.moveToThread(cls._thread)

        cls._thread.started.connect(cls._worker.run)
        cls._thread.finished.connect(cls._worker.deleteLater)
        cls._thread.finished.connect(cls._thread.deleteLater)
        cls._thread.finished.connect(cls._on_thread_finished)

        cls._thread.start()

    @classmethod
    def stop(cls) -> None:
        thread_running = cls._thread is not None and cls._thread.isRunning()
        if cls._worker is None or not thread_running:
            return

    @classmethod
    def _on_thread_finished(cls) -> None:
        cls._thread = None
        cls._worker = None
