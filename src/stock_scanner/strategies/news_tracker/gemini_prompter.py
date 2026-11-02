import json
import logging
import time

from config.playwright_config import Config
from src.stock_scanner.playwright.playwright_session import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import LLMResponse, NewsEntry
from src.stock_scanner.workers.worker_status import WorkerStatus

logger = logging.getLogger(__name__)


# zdefiniować locatory jako zmienne, oraz dodać do nich diagnostykę - screenshoty,
# aby w razie zmiany gemini, szybko zidentyfikować, który z nich jest nieaktualny
# Przejrzeć lokatory i dać precyzyjne odniesienia, a nie jeden z kilku
class GeminiPrompter:
    URL = "https://gemini.google.com/"

    def __init__(self) -> None:
        self.session = PlaywrightSession()

    def restart(self) -> None:
        logger.info("Restartowanie sesji Gemini...")
        self.session.close()
        self.session.start(self.URL, headless=True, context=False)
        self._handle_cookie_banner()
        self._wait_for_prompt_input()

    def start(self) -> None:
        logger.info("Start sesji gemini")
        self.session.start(self.URL, headless=True, context=False)
        self._handle_cookie_banner()
        self._wait_for_prompt_input()

    def send_prompt(self, prompt: str) -> None:
        try:
            prompt_input = self.session.page.locator("#prompt-textarea, div[contenteditable='true']").first
            prompt_input.wait_for(state="visible", timeout=Config.prompt_timeout)
            prompt_input.click()
            prompt_input.fill(prompt, timeout=Config.prompt_load_timeout)
            prompt_input.press("Enter")
        except Exception as exc:
            self._handle_error("Gemini: Nie udało się wysłać prompta", str(exc))

    def _wait_for_prompt_input(self) -> None:
        try:
            prompt_input = self.session.page.locator("#prompt-textarea, div[contenteditable='true']").first
            prompt_input.wait_for(state="visible", timeout=Config.page_load_timeout)
        except Exception as exc:
            self._handle_error("Gemini: Input niegotowy", str(exc))

    def refresh(self) -> None:
        self.session.page.goto(
            self.URL,
            timeout=Config.page_load_timeout,
            wait_until="domcontentloaded",
        )

        self._wait_for_prompt_input()

    def close(self) -> None:
        self.session.close()

    def _handle_cookie_banner(self) -> None:
        accept_button = self.session.page.locator('button[data-test-id="accept-button"]')

        try:
            accept_button.wait_for(state="visible", timeout=5000)
            accept_button.click(timeout=5000)
            accept_button.wait_for(state="hidden", timeout=5000)
            logger.info("Baner cookies obsłużony")

        except Exception as exc:
            self._handle_error("Gemini: Błąd cookie - przekroczono timeout", str(exc))

    def _wait_for_stable_response(self) -> bool:
        deadline = time.monotonic() + 60

        response = self.session.page.locator("message-content .markdown").last

        try:
            response.wait_for(state="visible", timeout=Config.prompt_timeout)
        except Exception as exc:
            self._handle_error("Gemini nie utworzył elementu odpowiedzi w wyznaczonym czasie.", str(exc))
            return False

        last_text = ""

        while time.monotonic() < deadline:
            last_text = response.inner_text().strip()
            is_valid = self._validate_response(last_text)
            self.session.page.wait_for_timeout(500)

            if is_valid:
                self.session.page.wait_for_timeout(100)
                return True

        self._handle_error("Gemini nie dał odpowiedzi w czasie 60s.", f"wygenerowana odpowiedź: {last_text}")
        return False

    def _handle_error(self, message: str, full_log: str) -> None:
        screenshot = self.session.page.screenshot(full_page=True)
        WorkerStatus.update("LLM", "Last error")
        WorkerStatus.update_llm_error_status(message, full_log, screenshot)
        logger.error(message + "\n" + full_log)
        self.refresh()

    def _is_generating(self) -> bool:
        stop_button = self.session.page.locator(
            'button[aria-label*="Stop"], button[aria-label*="stop"], button[data-test-id*="stop"]'
        )

        try:
            return any(stop_button.nth(i).is_visible() for i in range(stop_button.count()))
        except Exception as exc:
            self._handle_error("Gemini: nie udało się ustalić stanu generowania.", str(exc))
            return False

    def _validate_response(self, response: str) -> bool:
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            return False

        if not isinstance(parsed, dict):
            return False

        if set(parsed) != {"forecast", "justification"}:
            return False

        if parsed["forecast"] not in Config.valid_forecasts:
            return False

        if not isinstance(parsed["justification"], str):
            return False

        return True

    def _parse_response(self, response: str) -> LLMResponse:
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError("Gemini zwrócił niepoprawny JSON.") from exc

        forecast = parsed["forecast"]
        justification = parsed["justification"]

        return {
            "forecast": forecast,
            "justification": justification,
        }

    def process_entry(self, entry: NewsEntry) -> LLMResponse | None:
        content = entry["content"]

        full_prompt = f"{Config.gpw_prompt} \nFragment html do analizy: {content}"
        self.send_prompt(full_prompt)

        if not self._wait_for_stable_response():
            return None

        response = self.session.page.locator("message-content .markdown").last.inner_text().strip()
        parsed_response = self._parse_response(response)

        return parsed_response
