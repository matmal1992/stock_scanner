import logging

from src.stock_scanner.strategies.news_tracker.playwright_session import PlaywrightSession

logger = logging.getLogger(__name__)


class DAXEntryContentScraper:
    BASE_URL = "https://www.eqs-news.com/"
    page_load_timeout: float = 15_000

    def __init__(self) -> None:
        self.session = PlaywrightSession()

    def start(self) -> None:
        logger.info("Start sesji DAX entry content scraper")
        self.session.start(self.BASE_URL, headless=False)

    def close(self) -> None:
        self.session.close()

    def refresh(self) -> None:
        self.session.page.goto(
            self.BASE_URL,
            timeout=self.page_load_timeout,
            wait_until="domcontentloaded",
        )

    def scrape_content(self, url: str) -> str:
        content: str = "invalid content"
        page = self.session.page

        try:
            page.goto(url, timeout=self.page_load_timeout, wait_until="domcontentloaded")
            container = page.locator("div.news-details__content div.break-word.news_main")
            container.wait_for(state="attached", timeout=self.page_load_timeout)

            if container.count() > 0:
                content = container.inner_text().strip()
        except Exception as exc:
            logger.exception(f"DAX: błąd pobierania treści artykułu {url}: {exc}")

        return content
