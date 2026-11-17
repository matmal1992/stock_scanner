import logging

from src.stock_scanner.strategies.news_tracker.playwright_session import PlaywrightSession

logger = logging.getLogger(__name__)


class PAPEntryContentScraper:
    BASE_URL = "https://espiebi.pap.pl/"
    page_load_timeout: float = 15_000

    def __init__(self) -> None:
        self.session = PlaywrightSession()

    def start(self) -> None:
        logger.info("Start sesji PAP entry content scraper")
        self.session.start(self.BASE_URL, headless=True)

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

        page.goto(url, timeout=self.page_load_timeout, wait_until="domcontentloaded")
        container = page.locator("div.field-body-xml-content")
        container.wait_for(state="attached", timeout=self.page_load_timeout)

        if container.count() > 0:
            content = container.evaluate("(element) => element.outerHTML")

        return content
