import logging

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from src.stock_scanner.core.paths import get_browser_dir

logger = logging.getLogger(__name__)


class GeminiPrompter:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def start(self) -> None:
        """Uruchamia przeglądarkę i wchodzi na stronę Gemini."""
        self.playwright = sync_playwright().start()
        chrome_args = ["--disable-blink-features=AutomationControlled"]
        if self.headless:
            chrome_args.append("--headless=new")

        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )

        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=get_browser_dir() / "browser_user_data",
            headless=False,
            user_agent=user_agent,
            args=chrome_args,
            viewport={"width": 1280, "height": 800},
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.goto("https://gemini.google.com/", timeout=60000)

        # Sprawdzenie logowania przy pierwszym uruchomieniu
        if (
            "auth" in self.page.url
            or "accounts.google" in self.page.url
            or self.page.locator("text=Log in").count() > 0
        ):
            logger.error("Wykryto ekran logowania! Zaloguj się ręcznie w przeglądarce...")
            self.page.wait_for_selector("#prompt-textarea, div[contenteditable='true']", timeout=120000)
            logger.info("Zalogowano pomyślnie")

    def send_prompt(self, prompt: str) -> str:
        if self.page is None:
            raise RuntimeError("Przeglądarka nie została uruchomiona. Wywołaj najpierw metodę .start()")

        # 2. Odnalezienie i wypełnienie pola tekstowego
        prompt_input = self.page.locator("#prompt-textarea, div[contenteditable='true']").first
        prompt_input.wait_for(state="visible", timeout=30000)
        prompt_input.click()
        prompt_input.fill(prompt)

        # 3. Wysyłanie wiadomości
        send_button = self.page.locator(
            """button[data-testid="send-button"], button[aria-label="Wyślij wiadomość"], 
            button[aria-label="Send prompt"]"""
        ).first

        if send_button.is_visible():
            send_button.click()
        else:
            self.page.keyboard.press("Enter")

        # Oczekiwanie na zakończenie generowania (zniknięcie przycisku Stop)
        stop_button = self.page.locator('button[data-testid="stop-button"], button[aria-label*="Stop"]')
        try:
            stop_button.wait_for(state="hidden", timeout=15000)
        except Exception:
            logger.warning("Przekroczono czas oczekiwania na zniknięcie przycisku Stop")

        # Odczekanie chwili na dokończenie renderowania tekstu w DOM
        self.page.wait_for_timeout(15000)

        # Pobieramy OSTATNIĄ wiadomość asystenta
        response = self.page.locator("message-content .markdown").last

        try:
            response.wait_for(state="visible", timeout=120000)
        except Exception:
            logger.error("Nie znaleziono elementu .markdown z odpowiedzią Gemini.")

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
        new_chat_btn.click()

        logger.info("Otwieranie nowego chatu w Gemini...")
        # self.page.goto("https://gemini.google.com/", timeout=60000)

        # Czekamy aż nowe pole tekstowe będzie gotowe do interakcji
        self.page.wait_for_selector("#prompt-textarea, div[contenteditable='true']", timeout=30000)
