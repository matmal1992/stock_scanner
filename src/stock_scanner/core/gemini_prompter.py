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

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def start(self) -> None:
        """Uruchamia przeglądarkę i wchodzi na stronę Gemini."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)

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

        # Oczekiwanie na zakończenie generowania (zniknięcie przycisku Stop)
        # stop_button = self.page.locator('button[data-testid="stop-button"], button[aria-label*="Stop"]')
        # try:
        #     stop_button.wait_for(state="hidden", timeout=15000)
        # except Exception:
        #     logger.warning("Przekroczono czas oczekiwania na zniknięcie przycisku Stop")

        # # Odczekanie chwili na dokończenie renderowania tekstu w DOM
        # self.page.wait_for_timeout(5000)

        response = self.page.locator("message-content .markdown").last
        response.wait_for(state="visible", timeout=30_000)

        # try:
        #     response.wait_for(state="visible", timeout=15000)
        # except Exception:
        #     logger.error("Nie znaleziono elementu .markdown z odpowiedzią Gemini.")
        #     raise

        # self.page.wait_for_timeout(1000)

        # return response.inner_text()
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

        previous_text = ""
        stable_count = 0

        while time.monotonic() < deadline:
            current_text = response.inner_text().strip()

            if current_text == previous_text and current_text:
                stable_count += 1
            else:
                stable_count = 0

            previous_text = current_text

            if stable_count >= 2:
                try:
                    parsed = json.loads(current_text)

                    if isinstance(parsed, dict) and set(parsed) == {"forecast", "justification"}:
                        return current_text

                except json.JSONDecodeError:
                    pass

            self.page.wait_for_timeout(500)

        raise TimeoutError(
            f"Odpowiedź Gemini nie ustabilizowała się jako poprawny JSON. "
            f"Ostatnia odpowiedź: {previous_text[:1000]!r}"
        )
