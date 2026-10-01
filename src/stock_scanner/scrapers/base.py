from abc import ABC, abstractmethod
from typing import Final

from src.stock_scanner.scrapers.playwright import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import NewsEntry


class BaseScraper(ABC):
    BASE_URL: str
    REFRESH_TIMEOUT_MS: Final[int] = 10_000
    REFRESH_DELAY_MS: Final[int] = 1_000

    def __init__(self, session: PlaywrightSession) -> None:
        self.session = session

    def start(self) -> None:
        self.session.start(self.BASE_URL)

    def refresh(self) -> None:
        self._refresh_page()
        self._wait_after_refresh()

    def scrape(self) -> list[NewsEntry]:
        return self._scrape_entries()

    def close(self) -> None:
        self.session.close()

    @abstractmethod
    def _scrape_entries(self) -> list[NewsEntry]:
        raise NotImplementedError

    @abstractmethod
    def _refresh_page(self) -> None:
        raise NotImplementedError

    def _wait_after_refresh(self) -> None:
        self.session.page.wait_for_timeout(self.REFRESH_DELAY_MS)
