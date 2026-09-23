import logging
import re
from typing import Optional

from playwright.sync_api import BrowserContext, Locator, Page, Playwright, sync_playwright
from PySide6.QtCore import QObject, QThread, QTimer, Signal

from config.app_config import FILTERED_TITLE_SUBSTRINGS
from src.stock_scanner.strategies.news_tracker.entry_repo import (
    EntryRepository,
    NewsEntry,
)

logger = logging.getLogger(__name__)


class GPWWorker(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    URL = "https://espiebi.pap.pl/"
    INTERVAL_MS = 5_000

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo

        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self._timer: QTimer | None = None

    def run(self) -> None:
        self.log.emit("Start scrapowania komunikatów giełdowych z PAP...")

        try:
            self._start_browser()
            self._timer = QTimer()
            self._timer.setInterval(self.INTERVAL_MS)
            self._timer.timeout.connect(self._on_timer)
            self._scrape_and_save()
            self._timer.start()
            QThread.currentThread().exec()

        except Exception as exc:
            self.error.emit(f"PAP error: {exc}")

        finally:
            self._close_browser()
            self.finished.emit()

    def _start_browser(self) -> None:
        self.log.emit("PAP: uruchamianie przeglądarki...")

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(headless=True)

        self.context = self.browser.new_context()

        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

        self.page.goto(
            self.URL,
            timeout=15_000,
            wait_until="domcontentloaded",
        )

        self.page.wait_for_timeout(3_000)

        self.log.emit("PAP: przeglądarka uruchomiona")

    def _on_timer(self) -> None:
        try:
            self.log.emit("PAP: czas na kolejne pobieranie")

            self._refresh()

            self._scrape_and_save()

        except Exception as exc:
            self.error.emit(f"PAP error podczas odświeżania: {exc}")

    def _refresh(self) -> None:
        if self.page is None:
            raise RuntimeError("Przeglądarka nie została uruchomiona.")

        refresh_button = self.page.locator("#refreshHomeId a.refreshButton")
        refresh_button.wait_for(state="visible", timeout=10_000)
        refresh_button.click()

        refresh_datetime = self.page.locator("#refreshHomeId .refreshDateTime").inner_text().strip()
        self.log.emit(f"PAP: dane pobrano: {refresh_datetime}")

        self.page.wait_for_timeout(1_000)

    def _scrape_and_save(self) -> None:
        entries = self._scrape()

        self.log.emit(f"PAP: znaleziono {len(entries)} komunikatów")

        has_new = self._save_entries(entries)

        self.result.emit(has_new)

    def _scrape(self) -> list[NewsEntry]:
        if self.page is None:
            raise RuntimeError("Przeglądarka nie została uruchomiona.")

        day_blocks = self.page.locator(".view-report-listing div.day")
        day_count = day_blocks.count()

        results: list[NewsEntry] = []

        for d in range(day_count):
            day_block = day_blocks.nth(d)
            date_str = day_block.locator("h3").first.inner_text().strip()

            items = day_block.locator("ul.newsList li.news")
            item_count = items.count()

            for i in range(item_count):
                try:
                    item = items.nth(i)
                    entry = self._parse_item(item, date_str)

                    if entry is not None:
                        results.append(entry)

                except Exception as exc:
                    logger.error(f"PAP: błąd parsowania wpisu {i} z dnia {date_str}: {exc}")
                    self.log.emit(f"PAP: błąd parsowania wpisu {i}: {exc}")

        self.log.emit(f"PAP: znaleziono {len(results)} komunikatów")
        return results

    def _has_keywords(self, title: str) -> bool:
        title_lower = title.casefold()

        for substring in FILTERED_TITLE_SUBSTRINGS:
            if substring.casefold() in title_lower:
                return True

        return False

    def _parse_item(self, item: Locator, date_str: str) -> Optional[NewsEntry]:
        link_locator = item.locator("a.link")

        title = link_locator.inner_text().strip()
        link = link_locator.get_attribute("href")

        hour_str = item.locator("div.hour").first.inner_text().strip()

        if not link:
            return None

        full_published = f"{date_str} {hour_str}"
        llm_status = "-"

        if self._has_keywords(title):
            is_skipped = 1
        else:
            is_skipped = 0
            llm_status = "pending"

        return {
            "id": 0,
            "title": title,
            "link": self._absolute_url(link),
            "published": full_published,
            "source_type": "ESPI",
            "ticker": self._extract_ticker(title),
            "llm": llm_status,
            "justification": "-",
            "skipped": is_skipped,
        }

    def _extract_ticker(self, title: str) -> Optional[str]:
        if " - " not in title:
            return None

        ticker = title.split(" - ", 1)[0].strip()

        if not ticker:
            return None

        return ticker

    def _absolute_url(self, link: str) -> str:
        if link.startswith("http://"):
            return link

        if link.startswith("https://"):
            return link

        if link.startswith("//"):
            return "https:" + link

        if link.startswith("/"):
            return "https://espiebi.pap.pl" + link

        return link

    def _extract_date(self, text: str) -> str:
        match = re.search(
            r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}",
            text,
        )

        if match:
            return match.group(0)

        return ""

    def _save_entries(self, entries: list[NewsEntry]) -> bool:
        found_new = False

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    # if entry["skipped"] == 0:
                    #     send_telegram_message(entry)
                    # else:
                    #     logger.info(f"GPW: skipped: {entry['title']}")
                    found_new = True

            except Exception as exc:
                self.log.emit(f"PAP: błąd zapisu: {exc}")

        return found_new

    def stop(self) -> None:
        self.log.emit("PAP: zatrzymywanie workera...")

        if self._timer is not None:
            self._timer.stop()

        thread = QThread.currentThread()

        if thread is not None:
            thread.quit()

    def _close_browser(self) -> None:
        self.log.emit("PAP: zamykanie przeglądarki...")

        if self.context is not None:
            self.context.close()
            self.context = None

        if self.playwright is not None:
            self.playwright.stop()
            self.playwright = None

        self.page = None

        self.log.emit("PAP: przeglądarka zamknięta")


class GPWService(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self._thread: Optional[QThread] = None
        self.worker: Optional[GPWWorker] = None

    def start(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            self.log.emit("Automatyczne pobieranie PAP już działa")
            return False

        self.log.emit("Uruchamiam automatyczne pobieranie PAP")

        self._thread = QThread()
        self.worker = GPWWorker(self.entry_repo)

        self.worker.moveToThread(self._thread)
        self.worker.result.connect(self._on_worker_result)
        self.worker.error.connect(self._on_worker_error)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self._on_worker_finished)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.started.connect(self.worker.run)
        self._thread.start()

        return True

    def stop(self) -> None:
        if self.worker is None:
            self.log.emit("Automatyczne pobieranie PAP nie działa")

            return

        self.log.emit("PAP: zatrzymywanie automatycznego pobierania...")

        self.worker.stop()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _on_worker_result(self, has_new: bool) -> None:
        self.result.emit(has_new)

    def _on_worker_error(self, message: str) -> None:
        self.error.emit(message)

    def _on_worker_finished(self) -> None:
        if self._thread is not None:
            self._thread.quit()

    def _on_thread_finished(self) -> None:
        if self.worker is not None:
            self.worker.deleteLater()

        self._thread = None
        self.worker = None

        self.log.emit("Automatyczne pobieranie PAP zatrzymane")
        self.finished.emit()
