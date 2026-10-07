import logging
import re
from typing import Optional

from playwright.sync_api import Locator

from src.stock_scanner.scrapers.base import BaseScraper
from src.stock_scanner.scrapers.keywords import (
    GPW_SUBSTRINGS,
    has_keywords,
)
from src.stock_scanner.scrapers.playwright import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import NewsEntry

logger = logging.getLogger(__name__)


class PapEspiScraper(BaseScraper):
    BASE_URL = "https://espiebi.pap.pl/"
    CONTENT_SELECTOR = "div.field-body-xml-content"
    PAGE_LOAD_TIMEOUT = 10_000

    def __init__(self, session: PlaywrightSession) -> None:
        self.session = session

    def start(self) -> None:
        self.session.start(self.BASE_URL, headless=True)
        self._content_page = self.session.new_page()

    def close(self) -> None:
        if self._content_page is not None:
            self._content_page.close()

        self.session.close()

    def _refresh_page(self) -> None:
        refresh_button = self.session.page.locator("#refreshHomeId a.refreshButton")
        refresh_button.wait_for(state="visible", timeout=self.PAGE_LOAD_TIMEOUT)
        refresh_button.click()

        # refresh_datetime = self.session.page.locator("#refreshHomeId .refreshDateTime").inner_text().strip()
        # logger.info("PAP: dane pobrano: %s", refresh_datetime)

    def _scrape_entries(self) -> list[NewsEntry]:
        day_blocks = self.session.page.locator(".view-report-listing div.day")

        results: list[NewsEntry] = []

        for d in range(day_blocks.count()):
            day_block = day_blocks.nth(d)

            date_str = day_block.locator("h3").first.inner_text().strip()

            items = day_block.locator("ul.newsList li.news")

            for i in range(items.count()):
                try:
                    entry = self._parse_item(items.nth(i), date_str)

                    if entry is not None:
                        results.append(entry)

                except Exception as exc:
                    logger.exception(f"PAP: błąd parsowania wpisu {i}: {exc}")

        return results

    def scrape_content(self, url: str) -> str:
        if self._content_page is None:
            raise RuntimeError("PapEspiScraper nie został uruchomiony.")

        self._content_page.goto(url, timeout=self.PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")

        container = self._content_page.locator(self.CONTENT_SELECTOR)

        container.wait_for(state="attached", timeout=self.PAGE_LOAD_TIMEOUT)

        return container.evaluate("(element) => element.outerHTML")

    def _parse_item(self, item: Locator, date_str: str) -> Optional[NewsEntry]:
        link_locator = item.locator("a.link")

        title = link_locator.inner_text().strip()
        link = link_locator.get_attribute("href")

        hour_str = item.locator("div.hour").first.inner_text().strip()

        if not link:
            return None

        abs_url = self._absolute_url(link)
        is_skipped = has_keywords(title, GPW_SUBSTRINGS)

        return {
            "id": 0,
            "title": title,
            "link": abs_url,
            "published": f"{date_str} {hour_str}",
            "source_type": "ESPI",
            "ticker": self._extract_ticker(title),
            "llm": "-" if is_skipped else "pending",
            "justification": "-",
            "skipped": int(is_skipped),
            "content": None,
        }

    @staticmethod
    def _extract_ticker(title: str) -> Optional[str]:
        if " - " not in title:
            return None

        ticker = title.split(" - ", 1)[0].strip()

        return ticker or None

    @staticmethod
    def _absolute_url(link: str) -> str:
        if link.startswith(("http://", "https://")):
            return link

        if link.startswith("//"):
            return "https:" + link

        if link.startswith("/"):
            return "https://espiebi.pap.pl" + link

        return link

    @staticmethod
    def _extract_date(text: str) -> str:
        match = re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", text)

        if match:
            return match.group(0)

        return ""
