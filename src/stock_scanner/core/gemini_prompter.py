import json
import logging
import time

from src.stock_scanner.scrapers.playwright import PlaywrightSession
from src.stock_scanner.strategies.news_tracker.entry_repo import LLMResponse

logger = logging.getLogger(__name__)


# zdefiniować locatory jako zmienne, oraz dodać do nich diagnostykę - screenshoty,
# aby w razie zmiany gemini, szybko zidentyfikować, który z nich jest nieaktualny
# Przejrzeć lokatory i dać precyzyjne odniesienia, a nie jeden z kilku
# Dodatkowo - optymalizacja i zabezpieczenie algorytmu - timeouty itp
class GeminiPrompter:
    URL = "https://gemini.google.com/"

    PAGE_LOAD_TIMEOUT = 15_000
    PROMPT_TIMEOUT = 30_000
    RESPONSE_TIMEOUT = 60
    RECOVERY_TIMEOUT = 15_000

    VALID_FORECASTS = {
        "Silny spadek",
        "Spadek",
        "Neutralny",
        "Wzrost",
        "Silny wzrost",
    }

    def __init__(self) -> None:
        self.session = PlaywrightSession()

    def restart(self) -> None:
        logger.info("Restartowanie sesji Gemini...")
        self.session.close()
        self.session.start(self.URL, headless=False, context=True)
        self._handle_cookie_banner()
        self._wait_for_prompt_input()

    def start(self) -> None:
        self.session.start(self.URL, headless=False, context=True)
        self._handle_cookie_banner()
        self._wait_for_prompt_input()

    def send_prompt(self, prompt: str) -> LLMResponse:
        prompt_input = self.session.page.locator("#prompt-textarea, div[contenteditable='true']").first
        prompt_input.wait_for(state="visible", timeout=self.PROMPT_TIMEOUT)
        prompt_input.click()
        prompt_input.fill(prompt)
        prompt_input.press("Enter")

        stable_response = self._wait_for_stable_response()
        parsed_response = self._parse_response(stable_response)

        return parsed_response

    def _wait_for_prompt_input(self) -> None:
        prompt_input = self.session.page.locator("#prompt-textarea, div[contenteditable='true']").first
        prompt_input.wait_for(state="visible", timeout=self.RECOVERY_TIMEOUT)

    def refresh(self) -> None:
        self.session.page.goto(self.URL)

        try:
            self._handle_cookie_banner()
            self._wait_for_prompt_input()

        except Exception as exc:
            logger.warning(
                "Gemini: strona została odświeżona, ale interfejs nie jest gotowy: %s",
                exc,
            )

    def screenshot(self, name: str) -> None:
        self.session.screenshot(name)

    def _handle_cookie_banner(self) -> None:
        accept_button = self.session.page.locator('button[data-test-id="accept-button"]')

        try:
            accept_button.wait_for(state="visible", timeout=5000)
            accept_button.click()
            accept_button.wait_for(state="hidden", timeout=5000)

        except Exception:
            logger.debug("Baner cookies nie został wykryty.")

    def _wait_for_stable_response(self, timeout: int = 30000) -> str:
        deadline = time.monotonic() + timeout

        response = self.session.page.locator("message-content .markdown").last

        try:
            response.wait_for(state="visible", timeout=self.PROMPT_TIMEOUT)
        except TimeoutError as exc:
            raise TimeoutError("Gemini nie utworzył elementu odpowiedzi w wyznaczonym czasie.") from exc

        last_text = ""

        while time.monotonic() < deadline:
            last_text = response.inner_text().strip()

            if self._is_valid_response(last_text):
                return last_text

            self.session.page.wait_for_timeout(500)

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
