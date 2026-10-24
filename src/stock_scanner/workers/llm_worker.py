import logging
import threading

from PySide6.QtCore import QObject, QThread, Signal

from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry
from src.stock_scanner.strategies.news_tracker.gemini_prompter import GeminiPrompter
from src.stock_scanner.workers.telegram import TelegramBot
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class LLMWorker(QObject):
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


class LLMService(QObject):
    result = Signal(NewsEntry)

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self._thread: QThread | None = None
        self.worker: LLMWorker | None = None

    def start(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            return False

        self._thread = QThread()

        self.worker = LLMWorker(self.entry_repo)
        self.worker.moveToThread(self._thread)

        self._thread.started.connect(self.worker.run)
        self._thread.finished.connect(self.worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()

        return True

    def stop(self) -> None:
        if self.worker is None or not self.is_running():
            return

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _on_thread_finished(self) -> None:
        self._thread = None
        self.worker = None
