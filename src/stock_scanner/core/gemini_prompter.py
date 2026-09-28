import json
import logging
import time

from playwright.sync_api import BrowserContext, Locator, Page, Playwright, sync_playwright

logger = logging.getLogger(__name__)


# zdefiniować locatory jako zmienne, oraz dodać do nich diagnostykę,
# aby w razie zmiany gemini, szybko zidentyfikować, który z nich jest nieaktualny
# Przejrzeć lokatory i dać precyzyjne odniesienia, a nie jeden z kilku
# Dodatkowo - optymalizacja i zabezpieczenie algorytmu - timeouty itp
class GeminiPrompter:
    URL = "https://gemini.google.com/"

    VALID_FORECASTS = {
        "Silny spadek",
        "Spadek",
        "Neutralny",
        "Wzrost",
        "Silny wzrost",
    }

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def start(self) -> None:
        """Uruchamia przeglądarkę i wchodzi na stronę Gemini."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)

        self.context = self.browser.new_context()

        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

        self.page.goto(self.URL, timeout=15_000, wait_until="domcontentloaded")

        self.page.wait_for_timeout(3_000)
        self._handle_cookie_banner()

    def send_prompt(self, prompt: str) -> str:
        if self.page is None:
            raise RuntimeError("Przeglądarka nie została uruchomiona. Wywołaj najpierw metodę .start()")

        prompt_input = self.page.locator("#prompt-textarea, div[contenteditable='true']").first
        prompt_input.wait_for(state="visible", timeout=30000)
        prompt_input.click()
        prompt_input.fill(prompt)
        prompt_input.press("Enter")

        response = self.page.locator("message-content .markdown").last
        response.wait_for(state="visible", timeout=30_000)

        return self._wait_for_stable_response(response)

    def close(self) -> None:
        """Zamyka przeglądarkę."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

    def new_chat(self) -> None:
        if self.page is None:
            return

        self.page.locator('gem-nav-list-item[data-test-id="reset-button"]').click()
        self._confirm_new_chat()

        self.page.wait_for_selector("#prompt-textarea, div[contenteditable='true']", timeout=30000)

    def _handle_cookie_banner(self) -> None:
        if self.page is None:
            return

        accept_button = self.page.locator('button[data-test-id="accept-button"]')

        try:
            accept_button.wait_for(state="visible", timeout=5000)
            accept_button.click()
            accept_button.wait_for(state="hidden", timeout=5000)

        except Exception:
            logger.debug("Baner cookies nie został wykryty.")

    def _confirm_new_chat(self) -> None:
        if self.page is None:
            raise RuntimeError("Przeglądarka nie została uruchomiona.")

        confirm_button = self.page.locator('gem-button[data-test-id="confirm-button"]')

        confirm_button.wait_for(state="visible", timeout=10_000)
        confirm_button.click(timeout=10_000)

    def _wait_for_stable_response(self, response: Locator, timeout: int = 60) -> str:
        if self.page is None:
            raise RuntimeError("Przeglądarka nie została uruchomiona.")
        deadline = time.monotonic() + timeout
        last_text = ""

        while time.monotonic() < deadline:
            last_text = response.inner_text().strip()

            if self._is_valid_response(last_text):
                return last_text

            self.page.wait_for_timeout(500)

        raise TimeoutError(
            "Gemini nie zwrócił poprawnego JSON w wyznaczonym czasie. "
            f"Ostatnia odpowiedź: {last_text[:1000]!r}"
        )

    @classmethod
    def _is_valid_response(cls, response: str) -> bool:
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            return False

        if not isinstance(parsed, dict):
            return False

        if set(parsed) != {"forecast", "justification"}:
            return False

        if parsed["forecast"] not in cls.VALID_FORECASTS:
            return False

        if not isinstance(parsed["justification"], str):
            return False

        return True
