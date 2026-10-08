import logging

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from src.stock_scanner.core.gemini_prompter import GeminiPrompter
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry

logger = logging.getLogger(__name__)


class LLMWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    result = Signal(NewsEntry)

    INTERVAL_MS = 1_000

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.prompter = GeminiPrompter()
        self._timer: QTimer = QTimer(interval=self.INTERVAL_MS)

    def run(self) -> None:
        logger.info("LLM worker started")

        try:
            self.prompter.start()
            self._timer.timeout.connect(self._on_timer)
            self._timer.start()
            QThread.currentThread().exec()

        except Exception as exc:
            self.error.emit(f"LLM error: {exc}")

        finally:
            self.prompter.close()
            self.finished.emit()

    def _on_timer(self) -> None:
        pending = self.entry_repo.get_no_content_pending(limit=1)

        if not pending:
            return

        entry = pending[0]

        try:
            self.prompter._process_entry(entry)
        except Exception as exc:
            logger.exception("LLM worker error dla %s", entry["id"])
            self.error.emit(f"LLM worker error dla {entry['id']}: {exc}")
            self.prompter.screenshot(name=f"llm_worker_exc_{entry['id']}")

        finally:
            try:
                self.prompter.refresh()
            except Exception:
                logger.exception("Nie udało się odświeżyć LLM po wpisie %s", entry["id"])

    # def _process_entry(self, entry: NewsEntry) -> None:
    #     entry_id = entry["id"]
    #     content = entry["content"]

    #     self.log.emit(f"LLM: przetwarzanie wpisu {entry_id}")

    #     full_prompt = f"{gpw_prompt} Content: {content}"

    #     response = self.prompter.send_prompt(full_prompt)

    #     success = self.entry_repo.update_llm(entry_id, response)
    #     if not success:
    #         raise RuntimeError(f"Nie udało się zapisać wyniku dla {entry_id}")

    #     updated_entry = self.entry_repo.get_by_id(entry_id)
    #     if updated_entry is None:
    #         raise RuntimeError(f"Zapisano wynik, ale nie znaleziono wpisu {entry_id}")

    #     self.result.emit(updated_entry)
    #     self.log.emit(f"LLM: zakończono wpis {entry_id}")


class LLMService(QObject):
    log = Signal(str)
    error = Signal(str)
    finished = Signal()
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
        self.worker.log.connect(self.log)
        self.worker.error.connect(self.error)
        self.worker.finished.connect(self._thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.result.connect(self.result)

        self._thread.started.connect(self.worker.run)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()

        return True

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _on_thread_finished(self) -> None:
        self._thread = None
        self.worker = None

        self.finished.emit()
