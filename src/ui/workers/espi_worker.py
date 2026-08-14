from typing import Optional

from playwright.sync_api import Page, sync_playwright
from PySide6.QtCore import QObject, QThread, Signal

from src.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry


class ESPIWorker(QObject):
    result = Signal(list, bool)
    error = Signal(str)
    log = Signal(str)

    URL = "https://www.bankier.pl/gielda/wiadomosci/komunikaty-spolek"

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo

    def run(self) -> None:
        self.log.emit("Start scrapowania ESPI")

        try:
            entries = self._scrape()
            has_new = self._save_entries(entries)
            latest = self.entry_repo.get_latest_with_id("ESPI")
            self.result.emit(latest, has_new)

        except Exception as exc:
            self.error.emit(f"ESPI error: {exc}")

    def _scrape(self) -> list[NewsEntry]:
        results: list[NewsEntry] = []

        with sync_playwright() as p:
            browser = None

            try:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                self.log.emit("Owwieranie strony ESPI...")
                page.goto(self.URL, timeout=30000, wait_until="networkidle")
                self._accept_cookies(page)

                if not self._is_valid_page(page):
                    self.log.emit("Nieprawidłowa strona ESPI")
                    return results

                page.wait_for_selector("a.m-quotes-announcements-item__anchor")
                items = page.locator("li.m-quotes-announcements-list__item")

                count = min(items.count(), 5)
                self.log.emit(f"Znaleziono {count} komunikatów")

                for i in range(count):
                    item = items.nth(i)

                    try:
                        date_str = item.locator("span.m-quotes-announcements-item__date").inner_text()

                        title = item.locator("a.m-quotes-announcements-item__anchor").inner_text()

                        link = item.locator("a.m-quotes-announcements-item__anchor").get_attribute("href")

                        if not link:
                            self.log.emit(f"Brak linku dla elementu {i}")
                            continue

                        results.append(
                            {
                                "title": title,
                                "link": link,
                                "published": date_str,
                                "source_type": "ESPI",
                                "llm": "pending",
                                "sentiment": "-",
                            }
                        )

                    except Exception as exc:
                        self.log.emit(f"Błąd parsowania elementu {i}: {exc}")

            finally:
                if browser is not None:
                    browser.close()

        return results

    def _is_blocked(self, page: Page) -> bool:
        content = page.content().lower()

        blocked_keywords = [
            "access denied",
            "captcha",
            "verify you are human",
            "zablokowany",
        ]

        return any(word in content for word in blocked_keywords)

    def _save_entries(self, entries: list[NewsEntry]) -> bool:
        found_new = False

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    found_new = True
            except Exception as exc:
                self.log.emit(f"Błąd zapisu: {exc}")

        return found_new

    def _is_valid_page(self, page: Page) -> bool:
        try:
            locator = page.locator("li.m-quotes-announcements-list__item")

            if locator.count() > 0:
                return True
            else:
                if self._is_blocked(page):
                    page.screenshot(path="debug_blocked.png")
                    self.log.emit("Strona została zablokowana")
                    return False

                page.screenshot(path="debug_invalid_page.png")
                self.log.emit("To nie jest właściwa strona ESPI")
                return False

        except Exception as exc:
            self.log.emit(f"Błąd sprawdzania strony: {exc}")
            return False

    def _is_cookie_banner(self, page: Page) -> bool:
        selectors = ["button:has-text('Zaakceptuj i zamknij')", "text=Zaakceptuj i zamknij"]

        for selector in selectors:
            try:
                if page.locator(selector).count() > 0:
                    return True
            except Exception:
                pass

        return False

    def _accept_cookies(self, page: Page) -> None:
        if not self._is_cookie_banner(page):
            return

        selectors = ["button:has-text('Zaakceptuj i zamknij')", "text=Zaakceptuj i zamknij"]

        page.wait_for_timeout(3000)

        for selector in selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    page.wait_for_timeout(1000)
                    self.log.emit("Zaakceptowano cookies")
                    return

            except Exception as exc:
                self.log.emit(f"Błąd dla selektora {selector}: {exc}")

        self.log.emit("Nie udało się zaakceptować cookies")


class ESPIService(QObject):
    result = Signal(list, bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self._thread: Optional[QThread] = None
        self.worker: Optional[ESPIWorker] = None

    def start(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            self.log.emit("ESPI już działa")
            return False

        self._thread = QThread()
        self.worker = ESPIWorker(self.entry_repo)

        self.worker.moveToThread(self._thread)

        self.worker.result.connect(self.result)
        self.worker.error.connect(self.error)
        self.worker.log.connect(self.log)
        self.worker.result.connect(self._thread.quit)
        self.worker.error.connect(self._thread.quit)
        self.worker.result.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)

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
