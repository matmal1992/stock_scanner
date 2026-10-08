import logging

from src.stock_scanner.scrapers.config import Config
from src.stock_scanner.scrapers.playwright import PlaywrightSession

logger = logging.getLogger(__name__)


class PageContentScraper:
    BASE_URL = "https://espiebi.pap.pl/"

    def __init__(self, session: PlaywrightSession) -> None:
        self.session = session

    def start(self) -> None:
        self.session.start(self.BASE_URL, headless=True)

    def close(self) -> None:
        self.session.close()

    def scrape_content(self, url: str) -> str:
        content: str = "invalid content"
        page = self.session.page

        page.goto(url, timeout=Config.page_load_timeout, wait_until="domcontentloaded")

        container = page.locator("div.field-body-xml-content")
        container.wait_for(state="attached", timeout=Config.page_load_timeout)

        if container.count == 1:
            content = container.evaluate("(element) => element.outerHTML")

        return content
