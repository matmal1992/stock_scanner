import logging

from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.strategies.news_tracker.gemini_prompter import GeminiPrompter
from src.stock_scanner.workers.base_worker import BaseWorker
from src.stock_scanner.workers.telegram import TelegramBot
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


class LLMWorker(BaseWorker):
    INTERVAL_SECONDS = 1

    def __init__(self, entry_repo: EntryRepository) -> None:
        self._session = GeminiPrompter()
        self.entry_repo = entry_repo
        super().__init__(self._session, "LLM")

    def run(self) -> None:
        logger.info("LLM worker started")

        try:
            self._session.start()

            while not self._stop_event.wait(self.INTERVAL_SECONDS):
                total_pending = self.entry_repo.get_pending_number()
                WorkerStatus.update("LLM", "Loop")
                WorkerStatus.update("LLM", "Pending", str(total_pending))

                try:
                    pending = self.entry_repo.get_pending_with_content(limit=1)

                    if not pending:
                        continue

                    entry = pending[0]
                    response = self._session.process_entry(entry)
                    if response is None:
                        self._session.refresh()
                        continue

                    self.entry_repo.update_llm(entry["id"], response)

                    entry["llm"] = response["forecast"]
                    entry["justification"] = response["justification"]

                    TelegramBot.send_alert(entry)
                    WorkerStatus.update("LLM", "Last processed")
                    self._session.refresh()

                except Exception as exc:
                    logger.exception("LLM prompter exception: %s", exc)
                    try:
                        self._session.refresh()
                    except Exception:
                        logger.exception("Nie udało się odświeżyć LLM po błędzie")
                    continue

        except Exception as exc:
            logger.exception("LLM worker exception: %s", exc)

        finally:
            logger.info("Closing LLM session...")
            self._session.close()
