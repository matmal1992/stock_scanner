from typing import Optional

from playwright.sync_api import Page, sync_playwright
from PySide6.QtCore import QObject, QThread, Signal

from src.core.utils import date_str_to_int
from src.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry


class ESPIWorker(QThread):
    result = Signal(list, bool)
    error = Signal(str)
    log = Signal(str)

    URL = "https://www.bankier.pl/gielda/wiadomosci/komunikaty-spolek"

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.worker: ESPIWorker

    def run(self) -> None:
        print("Start scrapowania ESPI\n")

        try:
            entries = self._scrape()
            has_new = self._save_entries(entries)
            latest = self.entry_repo.get_latest_with_id("ESPI")
            self.result.emit(latest, has_new)

        except Exception as e:
            self.error.emit(f"ESPI error: {e}")

    def _scrape(self) -> list[NewsEntry]:
        results: list[NewsEntry] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(self.URL, timeout=30000, wait_until="networkidle")

            self._accept_cookies(page)

            page.wait_for_selector("a.m-quotes-announcements-item__anchor")
            items = page.locator("li.m-quotes-announcements-list__item")

            count = min(items.count(), 5)

            for i in range(count):
                item = items.nth(i)

                try:
                    date_str = item.locator("span.m-quotes-announcements-item__date").inner_text()

                    title = item.locator("a.m-quotes-announcements-item__anchor").inner_text()

                    link = item.locator("a.m-quotes-announcements-item__anchor").get_attribute("href")

                    if not link:
                        print("Link not found\n")
                        continue

                    results.append(
                        {
                            "title": title,
                            "link": link,
                            "published": date_str_to_int(date_str),
                            "source_type": "ESPI",
                        }
                    )

                except Exception as e:
                    print(f"Błąd parsowania elementu: {e}")
                    self.log.emit(f"Błąd parsowania elementu: {e}")

            browser.close()

        return results

    def _save_entries(self, entries: list[NewsEntry]) -> bool:
        found_new = False

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    found_new = True
            except Exception as e:
                print(f"Błąd zapisu: {e}")
                self.log.emit(f"Błąd zapisu: {e}")

        return found_new

    def _accept_cookies(self, page: Page) -> None:
        selectors = [
            "button:has-text('Zaakceptuj i zamknij')",
            "text=Zaakceptuj i zamknij",
        ]

        page.wait_for_timeout(3000)

        for selector in selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    page.wait_for_timeout(1000)
                    self.log.emit("Zaakceptowano cookies")
                    return
            except Exception:
                pass

        self.log.emit("Brak bannera cookies")


class ESPIService(QObject):
    result = Signal(list, bool)
    error = Signal(str)
    log = Signal(str)

    def __init__(self, entry_repo: EntryRepository):
        super().__init__()
        self.entry_repo = entry_repo
        self.worker: Optional[ESPIWorker] = None

    def run(self) -> None:
        self.worker = ESPIWorker(self.entry_repo)

        self.worker.result.connect(self.result)
        self.worker.error.connect(self.error)
        self.worker.log.connect(self.log)
        self.worker.finished.connect(self.worker.deleteLater)

        self.worker.start()
