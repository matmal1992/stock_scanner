import logging

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from src.stock_scanner.scrapers.playwright import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository

logger = logging.getLogger(__name__)


class ScraperWorker(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    def __init__(self, session: PlaywrightSession) -> None:
        self.session = session
        
    def start(self) -> None:
        self.session.start(self.BASE_URL, headless=True)
        self._content_page = self.session.new_page()

        self.scraper = scraper
        self.entry_repo = entry_repo
        self.interval_ms = interval_ms

        self._timer: QTimer | None = None

    def run(self) -> None:
        self.log.emit("Uruchamiam scrapera...")

        try:
            self.scraper.start()

            self._timer = QTimer()
            self._timer.setInterval(self.interval_ms)
            self._timer.timeout.connect(self._on_timer)

            self._scrape_and_save()
            self._timer.start()

            QThread.currentThread().exec()

        except Exception as exc:
            logger.exception("Błąd workera")
            self.error.emit(f"Scraper error: {exc}")

        finally:
            self.scraper.close()
            self.finished.emit()

    def _on_timer(self) -> None:
        try:
            self.log.emit("Scraper: kolejne pobieranie")

            self.scraper.refresh()
            self._scrape_and_save()

        except Exception as exc:
            logger.exception("Błąd podczas odświeżania")
            self.error.emit(f"Scraper error: {exc}")

    def _scrape_and_save(self) -> None:
        entries = self.scraper.scrape()

        self.log.emit(f"Scraper: znaleziono {len(entries)} komunikatów")

        has_new = False

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    has_new = True

            except Exception as exc:
                self.log.emit(f"Błąd zapisu: {exc}")

        self.result.emit(has_new)

    def stop(self) -> None:
        self.log.emit("Zatrzymywanie workera...")

        if self._timer is not None:
            self._timer.stop()

        thread = QThread.currentThread()

        if thread is not None:
            thread.quit()
