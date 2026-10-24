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
        prompt_input = self.session.page.locator("#prompt-textarea, div[contenteditable='true']").first
        prompt_input.wait_for(state="visible", timeout=Config.prompt_timeout)
        prompt_input.click()
        prompt_input.fill(prompt, timeout=Config.page_load_timeout)
        prompt_input.press("Enter")

    def _wait_for_prompt_input(self) -> None:
        prompt_input = self.session.page.locator("#prompt-textarea, div[contenteditable='true']").first
        prompt_input.wait_for(state="visible", timeout=Config.page_load_timeout)

    def refresh(self) -> None:
        self.session.page.goto(
            self.URL,
            timeout=Config.page_load_timeout,
            wait_until="domcontentloaded",
        )

        try:
            self._handle_cookie_banner()
            self._wait_for_prompt_input()

        except Exception as exc:
            logger.warning("Gemini: błąd cookie albo input niegotowy: %s", exc)

    def screenshot(self, name: str) -> None:
        self.session.screenshot(name)

    def close(self) -> None:
        self.session.close()

    def _handle_cookie_banner(self) -> None:
        accept_button = self.session.page.locator('button[data-test-id="accept-button"]')

        try:
            accept_button.wait_for(state="visible", timeout=5000)
            accept_button.click()
            accept_button.wait_for(state="hidden", timeout=5000)

        except Exception:
            logger.debug("Baner cookies nie został wykryty.")

    def _wait_for_stable_response(self) -> bool:
        deadline = time.monotonic() + 60

        response = self.session.page.locator("message-content .markdown").last

        try:
            response.wait_for(state="visible", timeout=Config.prompt_timeout)
        except TimeoutError:
            WorkerStatus.update("LLM", "Last error")
            logger.error("Gemini nie utworzył elementu odpowiedzi w wyznaczonym czasie.")
            return False

        last_text = ""
        last_validation_error = ""

        while time.monotonic() < deadline:
            last_text = response.inner_text().strip()
            is_valid, validation_error = self._validate_response(last_text)
            is_generating = self._is_generating()

            if is_valid and not is_generating:
                return True

            if not is_valid and not is_generating:
                WorkerStatus.update("LLM", "Last error")
                logger.error("Gemini wygenerował błędną odpowiedź: %r", last_text[:2000])
                logger.error("Gemini validation_error: %s", last_validation_error)
                return False

            last_validation_error = validation_error
            self.session.page.wait_for_timeout(500)

        WorkerStatus.update("LLM", "Last error")
        logger.error("Gemini nie dał odpowiedzi w czasie 60s.")
        return False

    def _is_generating(self) -> bool:
        stop_button = self.session.page.locator(
            'button[aria-label*="Stop"], button[aria-label*="stop"], button[data-test-id*="stop"]'
        )

        try:
            return any(stop_button.nth(i).is_visible() for i in range(stop_button.count()))
        except Exception:
            logger.exception("Gemini: nie udało się ustalić stanu generowania.")

            return True

    @classmethod
    def _validate_response(cls, response: str) -> tuple[bool, str]:
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError:
            return False, "odpowiedź nie jest poprawnym JSON-em"

        if not isinstance(parsed, dict):
            return False, "JSON nie jest obiektem"

        if set(parsed) != {"forecast", "justification"}:
            return False, "JSON ma nieprawidłowy zestaw pól"

        if parsed["forecast"] not in Config.valid_forecasts:
            return False, "nieprawidłowa wartość forecast"

        if not isinstance(parsed["justification"], str):
            return False, "justification nie jest tekstem"

        return True, "OK"

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
