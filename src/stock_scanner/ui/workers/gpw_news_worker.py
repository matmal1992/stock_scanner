import re
from typing import Optional

from playwright.sync_api import Locator, Page, sync_playwright
from PySide6.QtCore import QObject, QThread, QTimer, Signal

from src.stock_scanner.strategies.news_tracker.entry_repo import (
    EntryRepository,
    NewsEntry,
)


class NewsWorker(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)

    URL = "https://www.bankier.pl/gielda/wiadomosci"

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo

    def run(self) -> None:
        self.log.emit("Start scrapowania newsów giełdowych")

        try:
            entries = self._scrape()
            has_new = self._save_entries(entries)
            self.result.emit(has_new)

        except Exception as exc:
            self.error.emit(f"GPW News error: {exc}")

    def _scrape(self) -> list[NewsEntry]:
        results: list[NewsEntry] = []

        with sync_playwright() as p:
            browser = None

            try:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                self.log.emit("Otwieranie strony Bankier giełda - wiadomości...")
                page.goto(self.URL, timeout=30000, wait_until="networkidle")
                self._accept_cookies(page)

                if not self._is_valid_page(page):
                    self.log.emit("Nieprawidłowa strona Bankier giełda - wiadomości")
                    return results

                page.wait_for_selector("li.m-listing-article-list__item")
                items = self._get_news_items(page)

                count = min(items.count(), 5)

                self.log.emit(f"Znaleziono {count} wpisów")

                for i in range(count):
                    try:
                        item = items.nth(i)

                        entry = self._parse_item(item)

                        if entry is not None:
                            results.append(entry)

                    except Exception as exc:
                        self.log.emit(f"GPW News: Błąd parsowania wpisu {i}: {exc}")

            finally:
                if browser is not None:
                    browser.close()

        return results

    def _get_news_items(self, page: Page) -> Locator:
        return page.locator("li.m-listing-article-list__item")

    def _parse_item(self, item: Locator) -> Optional[NewsEntry]:
        """
        Parsuje pojedynczy news.
        """

        anchor = item.locator("a.m-listing-article-list__anchor")

        link = anchor.get_attribute("href")

        if not link:
            return None

        title = item.locator(".m-listing-article-list__title").inner_text().strip()

        if not title:
            return None

        # # Pomijamy linki nawigacyjne, notowania itd.
        # if not self._looks_like_news(title, link):
        #     return None

        published = item.locator(".m-listing-article-list__date-time").inner_text().strip()

        return {
            "id": 0,
            "title": title,
            "link": self._absolute_url(link),
            "published": published,
            "source_type": "NEWS",
            "ticker": None,
            "llm": "pending",
            "sentiment": "-",
        }

    # def _looks_like_news(self, title: str, link: str) -> bool:
    #     """
    #     Odrzuca elementy strony, które nie są newsami.
    #     """

    #     if not title:
    #         return False

    #     if "/wiadomosc/" not in link:
    #         return False

    #     ignored_titles = {
    #         "WIG",
    #         "WIG20",
    #         "WIG30",
    #         "MWIG40",
    #         "DAX",
    #         "NASDAQ",
    #         "SP500",
    #         "USD/PLN",
    #         "EUR/PLN",
    #         "CHF/PLN",
    #         "ZŁOTO",
    #         "ROPA",
    #     }

    #     if title.strip() in ignored_titles:
    #         return False

    #     return True

    def _extract_date(self, text: str) -> str:
        match = re.search(
            r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}",
            text,
        )

        if match:
            return match.group(0)

        return ""

    def _absolute_url(self, link: str) -> str:
        if link.startswith("http://"):
            return link

        if link.startswith("https://"):
            return link

        if link.startswith("//"):
            return "https:" + link

        if link.startswith("/"):
            return "https://www.bankier.pl" + link

        return link

    def _is_valid_page(self, page: Page) -> bool:
        try:
            # Tytuł strony
            if not page.get_by_role(
                "heading",
                name="Giełda - Wiadomości",
            ).count():
                if self._is_blocked(page):
                    page.screenshot(path="debug_news_blocked.png")

                    self.log.emit("Strona newsów została zablokowana")

                    return False

                page.screenshot(path="debug_news_invalid_page.png")

                self.log.emit("To nie jest właściwa strona newsów")

                return False

            return True

        except Exception as exc:
            self.log.emit(f"Błąd sprawdzania strony newsów: {exc}")

            return False

    def _is_blocked(self, page: Page) -> bool:
        content = page.content().lower()

        blocked_keywords = [
            "access denied",
            "captcha",
            "verify you are human",
            "zablokowany",
        ]

        return any(word in content for word in blocked_keywords)

    def _is_cookie_banner(self, page: Page) -> bool:
        selectors = [
            "button:has-text('Zaakceptuj i zamknij')",
            "text=Zaakceptuj i zamknij",
        ]

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

            except Exception as exc:
                self.log.emit(f"Błąd dla selektora {selector}: {exc}")

        self.log.emit("Nie udało się zaakceptować cookies")

    def _save_entries(self, entries: list[NewsEntry]) -> bool:
        found_new = False
        saved_count = 0

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    found_new = True
                    saved_count += 1

            except Exception as exc:
                self.log.emit(f"Błąd zapisu: {exc}")

        self.log.emit(f"Zapisano nowych wpisów: {saved_count}/{len(entries)}")

        return found_new


class NewsService(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    INTERVAL_MS = 60_000

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self._thread: Optional[QThread] = None
        self.worker: Optional[NewsWorker] = None

        self._timer = QTimer(self)
        self._timer.setInterval(self.INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer)

    def start(self) -> bool:
        if self._timer.isActive():
            self.log.emit("Automatyczne pobieranie newsów już działa")

            return False

        self.log.emit("Uruchamiam automatyczne pobieranie newsów")
        self._run_once()
        self._timer.start()

        return True

    def stop(self) -> None:
        self._timer.stop()

        if self._thread is not None and self._thread.isRunning():
            self.log.emit("NEWS: oczekiwanie na zakończenie bieżącego scrapowania")
        else:
            self.log.emit("Automatyczne pobieranie newsów zatrzymane")

    def is_running(self) -> bool:
        return self._timer.isActive() or (self._thread is not None and self._thread.isRunning())

    def _on_timer(self) -> None:
        self.log.emit("NEWS: czas na kolejne pobieranie")

        self._run_once()

    def _run_once(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            self.log.emit("NEWS: poprzednie scrapowanie jeszcze trwa")

            return

        self._thread = QThread()
        self.worker = NewsWorker(self.entry_repo)

        self.worker.moveToThread(self._thread)
        self.worker.result.connect(self._on_worker_result)
        self.worker.error.connect(self._on_worker_error)
        self.worker.log.connect(self.log)
        self.worker.result.connect(self._finish_worker)
        self.worker.error.connect(self._finish_worker)

        self._thread.started.connect(self.worker.run)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()

    def _on_worker_result(self, has_new: bool) -> None:
        self.result.emit(has_new)

    def _on_worker_error(self, message: str) -> None:
        self.error.emit(message)

    def _finish_worker(self) -> None:
        if self._thread is not None:
            self._thread.quit()

    def _on_thread_finished(self) -> None:
        if self.worker is not None:
            self.worker.deleteLater()

        self._thread = None
        self.worker = None

        self.finished.emit()
