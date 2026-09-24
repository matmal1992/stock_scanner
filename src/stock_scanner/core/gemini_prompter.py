import logging

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

logger = logging.getLogger(__name__)


# zdefiniować locatory jako zmienne, oraz dodać do nich diagnostykę,
# aby w razie zmiany gemini, szybko zidentyfikować, który z nich jest nieaktualny
# Przejrzeć lokatory i dać precyzyjne odniesienia, a nie jeden z kilku
# Dodatkowo - optymalizacja i zabezpieczenie algorytmu - timeouty itp
class GeminiPrompter:
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

        self.page.goto(
            "https://gemini.google.com/",
            timeout=15_000,
            wait_until="domcontentloaded",
        )

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
        stop_button = self.page.locator('button[data-testid="stop-button"], button[aria-label*="Stop"]')
        try:
            stop_button.wait_for(state="hidden", timeout=15000)
        except Exception:
            logger.warning("Przekroczono czas oczekiwania na zniknięcie przycisku Stop")

        # Odczekanie chwili na dokończenie renderowania tekstu w DOM
        self.page.wait_for_timeout(5000)

        # Pobieramy OSTATNIĄ wiadomość asystenta
        response = self.page.locator("message-content .markdown").last

        try:
            response.wait_for(state="visible", timeout=15000)
        except Exception:
            logger.error("Nie znaleziono elementu .markdown z odpowiedzią Gemini.")

        self.page.wait_for_timeout(1000)

        return response.inner_text()

    def close(self) -> None:
        """Zamyka przeglądarkę."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

    def new_chat(self) -> None:
        """Otwiera nowy chat i czeka na załadowanie pola wpisywania."""
        if self.page is None:
            return

        new_chat_btn = self.page.locator('gem-nav-list-item[data-test-id="new-chat-button"]')
        try:
            new_chat_btn.wait_for(state="visible", timeout=5000)

            if not new_chat_btn.is_enabled():
                logger.warning("Przycisk 'New chat' jest nieaktywny.")
                return

            new_chat_btn.click(timeout=5000)

        except Exception as e:
            logger.warning(
                f"Nie można kliknąć przycisku 'New chat'. " f"Kontynuuję działanie programu. Powód: {e}"
            )
            return

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
