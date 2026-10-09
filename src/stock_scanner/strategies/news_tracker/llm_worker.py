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
        self._timer: QTimer = QTimer(self, interval=self.INTERVAL_MS)

    def run(self) -> None:
        logger.info("LLM worker started")

        try:
            self.prompter.start()
            self._timer.timeout.connect(self._on_timer)
            self._timer.start()
            logger.info("LLM timer uruchomiony")

        except Exception as exc:
            logger.exception("Nie udało się uruchomić LLM workera")
            self.error.emit(f"LLM error: {exc}")
            self._finish()

    def _on_timer(self) -> None:
        entry: NewsEntry | None = None

        try:
            pending = self.entry_repo.get_no_content_pending(limit=1)

            if not pending:
                return

            entry = pending[0]
            response = self.prompter.process_entry(entry)
            self.entry_repo.update_llm(entry["id"], response)
            self.log.emit(f"LLM: zakończono wpis {entry['id']}")
        except Exception as exc:
            entry_id = entry["id"] if entry is not None else "pending entries"
            logger.exception("LLM worker error dla %s", entry_id)
            self.error.emit(f"LLM worker error dla {entry_id}: {exc}")

            if entry is not None:
                try:
                    self.prompter.screenshot(name=f"llm_worker_exc_{entry['id']}")
                except Exception:
                    logger.exception("Nie udało się wykonać screenshotu dla wpisu %s", entry["id"])

        finally:
            if entry is not None:
                try:
                    self.prompter.refresh()
                except Exception:
                    logger.exception("Nie udało się odświeżyć LLM po wpisie %s", entry["id"])

    def stop(self) -> None:
        self.log.emit("Zatrzymywanie LLM workera...")
        self._finish()

    def _finish(self) -> None:
        # if self._is_finished:
        #     return

        # self._is_finished = True
        self._timer.stop()

        try:
            self.prompter.close()
        except Exception:
            logger.exception("Błąd podczas zamykania LLM promptera")

        self.finished.emit()


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
            self.log.emit("LLM już działa")
            return False

        self.log.emit("Uruchamiam LLM...")
        self._thread = QThread()

        self.worker = LLMWorker(self.entry_repo)
        self.worker.moveToThread(self._thread)
        # self.worker.stop_requested.connect(self.worker.stop)
        self.worker.log.connect(self.log)
        self.worker.error.connect(self.error)
        self.worker.finished.connect(self._thread.quit)
        self.worker.result.connect(self.result)

        self._thread.started.connect(self.worker.run)
        self._thread.finished.connect(self.worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()

        return True

    def stop(self) -> None:
        if self.worker is None or not self.is_running():
            return

        # self.worker.stop_requested.emit()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _on_thread_finished(self) -> None:
        self._thread = None
        self.worker = None

        self.finished.emit()
