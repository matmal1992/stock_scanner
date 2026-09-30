import logging
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from src.stock_scanner.core.paths import application_dir

logger = logging.getLogger(__name__)


# Dodać osobny logger dla playwright i zrobić okno w gui tylko dla logów
class PlaywrightSession:
    PAGE_LOAD_TIMEOUT = 15_000
    SCREENSHOTS_DIR = Path(application_dir() / "screens")

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

    def start(self, url: str, hidden: bool = False) -> Page:
        if self.is_running:
            raise RuntimeError("Sesja Playwright jest już uruchomiona.")

        try:
            self._playwright = sync_playwright().start()

            self._browser = self._playwright.chromium.launch(headless=hidden, args="--start-minimized")

            self._context = self._browser.new_context()

            self._page = self._context.new_page()

            self._page.goto(url, timeout=self.PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")

            self._page.wait_for_timeout(3_000)

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

    def refresh_page(self) -> bool:
        if self._page is None:
            logger.warning("Refresh pominięty: strona Playwright nie istnieje.")
            return False

        try:
            self._page.reload(timeout=self.PAGE_LOAD_TIMEOUT, wait_until="domcontentloaded")
            return True

        except Exception as exc:
            logger.error("Refresh nie powiódł się: %s", exc)
            return False

    def screenshot(self, name: str) -> Path | None:
        if self._page is None:
            logger.warning("Screenshot pominięty: strona Playwright nie istnieje.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        self.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

        path = self.SCREENSHOTS_DIR / f"{timestamp}_{name}.png"

        try:
            self._page.screenshot(path=str(path), full_page=True)

            logger.info("Screenshot zapisany: %s", path)

            return path

        except Exception:
            logger.exception("Nie udało się wykonać screenshotu: %s", path)
            return None
