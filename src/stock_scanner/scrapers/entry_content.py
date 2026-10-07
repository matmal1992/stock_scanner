import logging

from src.stock_scanner.scrapers.playwright import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository

logger = logging.getLogger(__name__)


class PageContentScraper:
    def __init__(self, repository: EntryRepository, session: PlaywrightSession) -> None:
        self.entry_repo = repository
        self.session = session

    def run(self) -> None:
        entries = self.entry_repo.get_entries_without_content()

        for entry in entries:
            try:
                content = self._scrape_content(entry["link"])

                self.entry_repo.update_content(
                    entry["id"],
                    content,
                )

            except Exception:
                logger.exception(
                    "Nie udało się pobrać contentu dla entry %s: %s",
                    entry["id"],
                    entry["link"],
                )

    def _scrape_content(self, url: str) -> str:
        page = self.session.page

        page.goto(
            url,
            timeout=15_000,
            wait_until="domcontentloaded",
        )

        container = page.locator("div.field-body-xml-content")

        container.wait_for(
            state="attached",
            timeout=15_000,
        )

        return container.evaluate("(element) => element.outerHTML")
