import logging
import time

from playwright.sync_api import sync_playwright

from src.stock_scanner.core.paths import configure_environment, get_browser_dir

logger = logging.getLogger(__name__)

GEMINI_URL = "https://gemini.google.com/"
PAP_URL = "https://espiebi.pap.pl/node/737428"


def main() -> None:
    with sync_playwright() as playwright:
        logger.info("Uruchamiam Chromium...")

        context = playwright.chromium.launch_persistent_context(
            user_data_dir=get_browser_dir() / "browser_user_data",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 800},
        )

        page = context.pages[0] if context.pages else context.new_page()

        logger.info("Otwieram Gemini...")
        page.goto(GEMINI_URL, timeout=60000)

        # Dajemy przeglądarce chwilę na załadowanie aplikacji
        page.wait_for_timeout(3000)

        # Czekamy na pole promptu.
        # Jeżeli nie jesteś zalogowany, możesz zalogować się ręcznie.
        prompt_input = page.locator("#prompt-textarea, div[contenteditable='true'], textarea").first

        try:
            prompt_input.wait_for(state="visible", timeout=15000)
        except Exception:
            logger.warning(
                "Nie znaleziono pola promptu. Jeżeli Gemini pokazuje ekran logowania, zaloguj się ręcznie."
            )

            # Czekamy dłużej na ręczne zalogowanie
            prompt_input.wait_for(state="visible", timeout=120000)

        logger.info("Gemini jest gotowe.")

        prompt = f"""
            Otwórz i przeanalizuj poniższy link:

            {PAP_URL}

            Chcę sprawdzić, czy masz dostęp do jego właściwej treści.
            Nie zgaduj i nie korzystaj tylko z wyników wyszukiwania.

            Napisz:
            1. czy udało Ci się otworzyć stronę,
            2. jaki jest tytuł komunikatu,
            3. jaka jest data komunikatu,
            4. kto jest jego autorem/nadawcą, jeśli informacja jest dostępna,
            5. podaj krótkie streszczenie treści.
            """

        logger.info("Wysyłam prompt do Gemini...")

        prompt_input.click()
        prompt_input.fill(prompt)

        # Próbujemy znaleźć przycisk wysyłania.
        send_button = page.locator(
            'button[data-testid="send-button"], '
            'button[aria-label="Wyślij wiadomość"], '
            'button[aria-label="Send prompt"], '
            'button[aria-label*="Wyślij"], '
            'button[aria-label*="Send"]'
        ).first

        if send_button.count() > 0 and send_button.is_visible():
            logger.info("Klikam przycisk wysyłania.")
            send_button.click()
        else:
            logger.info("Nie znaleziono przycisku wysyłania — używam Enter.")
            prompt_input.press("Enter")

        response = page.locator("message-content .markdown").last

        try:
            response.wait_for(
                state="visible",
                timeout=120000,
            )
        except Exception:
            logger.error("Nie znaleziono elementu .markdown z odpowiedzią Gemini.")

        # Dajemy Gemini czas na zakończenie generowania.
        page.wait_for_timeout(10000)

        if response.count() > 0:
            response = page.locator("message-content .markdown").last

            print("\n========== ODPOWIEDŹ GEMINI ==========\n")
            print(response.inner_text())
            print("\n=======================================\n")
        else:
            logger.error("Nie znaleziono odpowiedzi Gemini.")

        time.sleep(30)

        context.close()


if __name__ == "__main__":
    configure_environment()
    main()
