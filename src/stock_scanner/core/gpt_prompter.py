import logging

from playwright.sync_api import BrowserContext, Page, Playwright, sync_playwright

from src.stock_scanner.core.paths import get_browser_dir

logger = logging.getLogger(__name__)


class GPTPrompter:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def start(self) -> None:
        """Uruchamia przeglądarkę i wchodzi na stronę ChatGPT."""
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=get_browser_dir() / "browser_user_data",
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        self.page.goto("https://chatgpt.com/", timeout=60000)

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

        # 1. Pobieramy obecny obiekt odpowiedzi oraz ich liczbę
        responses = self.page.locator('[data-message-author-role="assistant"]')
        initial_responses_count = responses.count()

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

        # 4. Czekamy na dodanie NOWEJ odpowiedzi przy użyciu czystej metody Playwright .nth()
        target_index = initial_responses_count  # 0-indexed: np. dla 0 starych odpowiedzi celujemy w indeks 0
        new_response = responses.nth(target_index)
        new_response.wait_for(state="attached", timeout=30000)

        # Oczekiwanie na zakończenie generowania (zniknięcie przycisku Stop)
        stop_button = self.page.locator('button[data-testid="stop-button"], button[aria-label*="Stop"]')
        try:
            stop_button.wait_for(state="hidden", timeout=15000)
        except Exception:
            logger.warning("Przekroczono czas oczekiwania na zniknięcie przycisku Stop")

        # Odczekanie chwili na dokończenie renderowania tekstu w DOM
        self.page.wait_for_timeout(1000)

        # Pobieramy OSTATNIĄ wiadomość asystenta
        responses = self.page.locator('[data-message-author-role="assistant"]')
        last_response = responses.last
        last_response.wait_for(state="attached", timeout=10000)

        if last_response.locator(".markdown").count() > 0:
            return last_response.locator(".markdown").last.inner_text().strip()

        return last_response.inner_text().strip()

    def close(self) -> None:
        """Zamyka przeglądarkę."""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
