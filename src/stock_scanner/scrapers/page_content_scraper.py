import logging

from src.stock_scanner.scrapers.config import Config
from src.stock_scanner.scrapers.playwright import PlaywrightSession

logger = logging.getLogger(__name__)


class PageContentScraper:
    BASE_URL = "https://espiebi.pap.pl/"

    def __init__(self, session: PlaywrightSession) -> None:
        self.session = session

    def start(self) -> None:
        logger.info("Start wywołany")
        self.session.start(self.BASE_URL, headless=False)

    def close(self) -> None:
        self.session.close()

    def scrape_content(self, url: str) -> str:
        content: str = "invalid content"
        page = self.session.page

        logger.info(f"scrape content entered with url: {url}")

        logger.info("Rozpoczynam nawigację do komunikatu")

        try:
            response = page.goto(url, timeout=Config.page_load_timeout, wait_until="domcontentloaded")
        except Exception:
            logger.exception("CRASH podczas page.goto(): %s", url)
            raise

        logger.info("Nawigacja zakończona, status HTTP: %s", response.status if response else "brak")

        container = page.locator("div.field-body-xml-content")
        logger.info("Oczekiwanie na kontener treści komunikatu")
        container.wait_for(state="attached", timeout=Config.page_load_timeout)

        if container.count() > 0:
            logger.info("Container znaleziony")
            content = container.evaluate("(element) => element.outerHTML")

        return content
