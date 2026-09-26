import logging

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

logger = logging.getLogger(__name__)


# Dodać osobny logger dla playwright i zrobić okno w gui tylko dla logów
class PlaywrightSession:
    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Sesja Playwright nie została uruchomiona.")

        return self._page

    @property
    def is_running(self) -> bool:
        return self._playwright is not None

    def start(
        self,
        url: str,
        hidden: bool = False,
        timeout: int = 15_000,
        wait_after_load: int = 3_000,
    ) -> Page:
        if self.is_running:
            raise RuntimeError("Sesja Playwright jest już uruchomiona.")

        try:
            self._playwright = sync_playwright().start()

            self._browser = self._playwright.chromium.launch(headless=hidden)

            self._context = self._browser.new_context()

            self._page = self._context.new_page()

            self._page.goto(url, timeout=timeout, wait_until="domcontentloaded")

            if wait_after_load > 0:
                self._page.wait_for_timeout(wait_after_load)

            return self._page

        except Exception:
            self.close()
            raise

    def close(self) -> None:
        if self._context is not None:
            self._context.close()
            self._context = None

        if self._browser is not None:
            self._browser.close()
            self._browser = None

        if self._playwright is not None:
            self._playwright.stop()
            self._playwright = None

        self._page = None
