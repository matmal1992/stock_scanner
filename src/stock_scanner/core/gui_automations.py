import logging

from src.stock_scanner.core.paths import configure_environment
from src.stock_scanner.scrapers.playwright import PlaywrightSession

logger = logging.getLogger(__name__)

PAP_URL = "https://espiebi.pap.pl/node/737428"


def main() -> None:
    session = PlaywrightSession()
    try:
        page = session.start(
            url=PAP_URL,
            headless=False,
            context=False,
        )

        container = page.locator("div.field-body-xml-content")

        container.wait_for(state="attached")

        raw_html = container.evaluate("(element) => element.outerHTML")

        logger.info("Pobrano raw HTML.")
        logger.info("Długość raw HTML: %d znaków", len(raw_html))

        print(raw_html)

    finally:
        session.close()


if __name__ == "__main__":
    configure_environment()
    main()
