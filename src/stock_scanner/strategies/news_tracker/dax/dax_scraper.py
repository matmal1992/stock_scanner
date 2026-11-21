import logging
from typing import Optional

from playwright.sync_api import Locator
from PySide6.QtCore import QObject

from src.stock_scanner.strategies.news_tracker.entry_repo import NewsEntry
from src.stock_scanner.strategies.news_tracker.playwright_session import PlaywrightSession

logger = logging.getLogger(__name__)


class DaxScraper(QObject):
    BASE_URL = "https://www.eqs-news.com/"
    EXCLUDED_CATEGORIES = {"fr regulatory", "uk regulatory"}
    page_load_timeout: float = 15_000

    ALLOWED_CATEGORIES = {"ADHOC", "ANNOUNCEMENT", "WPUEG", "INTERNATIONAL"}

    def __init__(self) -> None:
        super().__init__()
        self.session = PlaywrightSession()

    def start(self) -> None:
        logger.info("Start sesji DAX scraper")
        self.session.start(self.BASE_URL, headless=False)
        # self.handle_cookies()
        self.set_filters()

    def close(self) -> None:
        self.session.close()

    def refresh_page(self) -> None:
        self.session.page.goto(
            self.BASE_URL,
            timeout=self.page_load_timeout,
            wait_until="domcontentloaded",
        )
        self.set_filters()

    def scrape_entries(self) -> list[NewsEntry]:
        items = self.session.page.locator('a[data-wio="news-feed-list-item"]')

        results: list[NewsEntry] = []

        for i in range(10):
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
        return category.lower() in self.EXCLUDED_CATEGORIES

    @staticmethod
    def _absolute_url(link: str) -> str:
        if link.startswith(("http://", "https://")):
            return link

        if link.startswith("//"):
            return "https:" + link

        return link

    def set_filters(self) -> None:
        logger.info("DAX: Configuring EQS filters")

        page = self.session.page
        modal = page.locator("[data-advanced-filter-modal-body]")

        if not modal.is_visible():
            page.locator('[data-wio="advance-filter-button"]').click()
            modal.wait_for(state="visible", timeout=self.page_load_timeout)

        category_dropdown = modal.locator("[data-filter-dropdown]").first
        dropdown_content = category_dropdown.locator("[data-dropdown-content]")

        if not dropdown_content.is_visible():
            category_dropdown.locator("[data-dropdown-anchor]").click()

        checkboxes = modal.locator('input[name="checkbox-categories[]"]')
        checkboxes.first.wait_for(state="attached", timeout=self.page_load_timeout)

        for i in range(checkboxes.count()):
            checkbox = checkboxes.nth(i)

            category = checkbox.get_attribute("value")
            checkbox_id = checkbox.get_attribute("id")

            if not category or not checkbox_id:
                continue

            should_be_checked = category in self.ALLOWED_CATEGORIES
            is_checked = checkbox.is_checked()

            if is_checked == should_be_checked:
                continue

            label = modal.locator(f'label[for="{checkbox_id}"]')
            label.click()

        page.locator('[data-wio="adv-filter-elem-button-apply"]').click()

        logger.info("DAX: Filters applied successfully")
