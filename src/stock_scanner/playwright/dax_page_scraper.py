import logging
from typing import Optional

from playwright.sync_api import Locator
from PySide6.QtCore import QObject

from config.playwright_config import Config
from src.stock_scanner.playwright.playwright_session import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import NewsEntry

logger = logging.getLogger(__name__)


class DaxScraper(QObject):
    BASE_URL = "https://www.eqs-news.com/"
    ALLOWED_CATEGORIES = {"corporate", "ad-hoc"}

    def __init__(self) -> None:
        super().__init__()
        self.session = PlaywrightSession()

    def start(self) -> None:
        logger.info("Start sesji DAX scraper")
        self.session.start(self.BASE_URL, headless=False)

    def close(self) -> None:
        self.session.close()

    def refresh_page(self) -> None:
        self.session.page.goto(
            self.BASE_URL,
            timeout=Config.page_load_timeout,
            wait_until="domcontentloaded",
        )

    def scrape_entries(self) -> list[NewsEntry]:
        items = self.session.page.locator('a[data-wio="news-feed-list-item"]')

        results: list[NewsEntry] = []

        for i in range(items.count(), 10):
            try:
                entry = self._parse_item(items.nth(i))

                if entry is not None:
                    results.append(entry)

            except Exception as exc:
                logger.exception(f"DAX: błąd parsowania wpisu {i}: {exc}")

        return results

    def _parse_item(self, item: Locator) -> Optional[NewsEntry]:
        title_locator = item.locator("p.news__heading")
        title = title_locator.inner_text().strip()

        if not title:
            return None

        link = item.get_attribute("href")

        if not link:
            return None

        company_locator = item.locator(".news__company")
        ticker = company_locator.inner_text().strip() if company_locator.count() > 0 else None

        date_locator = item.locator("xpath=preceding-sibling::p[contains(@class, 'news__date')][1]")

        date_str = date_locator.inner_text().strip() if date_locator.count() > 0 else ""

        hour_locator = item.locator(".news__time")

        hour_str = hour_locator.inner_text().strip() if hour_locator.count() > 0 else ""

        published = f"{date_str} {hour_str}".strip()

        abs_url = self._absolute_url(link)

        return {
            "id": 0,
            "title": title,
            "link": abs_url,
            "published": published,
            "source_type": "DAX",
            "ticker": ticker,
            "llm": "pending",
            "justification": "-",
            "content": None,
        }

    def skip(self, item: Locator) -> bool:
        category = item.get_attribute("data-news-category") or ""
        return category.lower() not in self.ALLOWED_CATEGORIES

    @staticmethod
    def _absolute_url(link: str) -> str:
        if link.startswith(("http://", "https://")):
            return link

        if link.startswith("//"):
            return "https:" + link

        if link.startswith("/"):
            return "https://espiebi.pap.pl" + link

        return link
