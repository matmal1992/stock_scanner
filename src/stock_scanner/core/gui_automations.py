import logging
import traceback

from src.stock_scanner.core.paths import configure_environment
from src.stock_scanner.scrapers.playwright import PlaywrightSession

logger = logging.getLogger(__name__)

PAP_URL = "https://espiebi.pap.pl/node/739060"


def main() -> None:
    session = PlaywrightSession()
    try:
        print("1. Uruchamiam przeglądarkę...", flush=True)
        page = session.start(
            url="https://espiebi.pap.pl/",
            headless=False,
            context=False,
        )

        print("2. Przeglądarka uruchomiona.", flush=True)
        print("Aktualny URL:", page.url, flush=True)
        print("3. Wywołuję page.goto()...", flush=True)

        response = page.goto(PAP_URL, timeout=30000, wait_until="domcontentloaded")
        print("4. Nawigacja zakończona.", flush=True)
        print("STATUS:", response.status if response else None, flush=True)
        print("URL:", page.url, flush=True)
        # input("Naciśnij Enter, aby zamknąć przeglądarkę...")
    except Exception:
        traceback.print_exc()
        if page is not None:
            try:
                print("URL po błędzie:", page.url, flush=True)
                page.screenshot(path="debug_playwright.png")
                print("Zapisano debug_playwright.png", flush=True)
            except Exception:
                print("Nie udało się wykonać diagnostyki strony.")
                traceback.print_exc()
        raise
        # container = page.locator("div.field-body-xml-content")

        # container.wait_for(state="attached")

        # raw_html = container.evaluate("(element) => element.outerHTML")

        # logger.info("Pobrano raw HTML.")
        # logger.info("Długość raw HTML: %d znaków", len(raw_html))

        # print(raw_html)

    finally:
        print("5. Zamykam sesję Playwright...", flush=True)
        session.close()


if __name__ == "__main__":
    configure_environment()
    main()
