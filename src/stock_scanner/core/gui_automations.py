import logging
import os
import time

import pyperclip
from playwright.sync_api import sync_playwright

from src.stock_scanner.core.gpt_prompter import GPTPrompter
from src.stock_scanner.core.paths import configure_environment

logger = logging.getLogger(__name__)


def send_prompt_and_copy_response(prompt: str = "Test prompt", headless: bool = False) -> str:
    # Tworzymy katalog na zapisanie sesji (zalogowania)
    user_data_dir = os.path.join(os.getcwd(), "browsers/browser_user_data")

    with sync_playwright() as p:
        # Używamy trwałego kontekstu zamiast p.chromium.launch()
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
            permissions=["clipboard-read", "clipboard-write"],
        )

        page = context.pages[0] if context.pages else context.new_page()

        page.goto("https://chatgpt.com/", timeout=60000)

        # 1. Obsługa zalogowania / przekierowania
        # Jeśli pojawi się strona logowania, dajemy użytkownikowi czas na ręczne zalogowanie
        if "auth" in page.url or "accounts.google" in page.url or page.locator("text=Log in").count() > 0:
            print("Wykryto ekran logowania! Zaloguj się ręcznie w oknie przeglądarki...")
            # Czekamy aż pojawi się pole promptu po zalogowaniu
            page.wait_for_selector("#prompt-textarea, div[contenteditable='true']", timeout=120000)
            print("Zalogowano pomyślnie! Sesja została zapisana.")

        # 2. Odnajdywanie i wypełnianie pola promptu
        prompt_input = page.locator("#prompt-textarea, div[contenteditable='true']").first
        prompt_input.wait_for(state="visible", timeout=30000)
        prompt_input.click()
        prompt_input.fill(prompt)

        # 3. Wysyłanie wiadomości
        send_button = page.locator(
            """button[data-testid="send-button"], button[aria-label="Wyślij wiadomość"], 
            button[aria-label="Send prompt"]"""
        ).first

        if send_button.is_visible():
            send_button.click()
        else:
            page.keyboard.press("Enter")

        # 4. Oczekiwanie na przycisk "Kopiuj" pod odpowiedzią
        copy_button = page.locator('button[aria-label*="Kopiuj"], button[aria-label*="Copy"]').last
        copy_button.wait_for(state="visible", timeout=60000)

        # 5. Kliknięcie i pobranie ze schowka
        copy_button.click()
        page.wait_for_timeout(1000)
        response_text = pyperclip.paste()

        context.close()
        return response_text


if __name__ == "__main__":
    configure_environment()

    bot = GPTPrompter(headless=False)
    bot.start()

    # Pierwszy prompt
    odpowiedz_1 = bot.send_prompt("Test prompt")
    print("\n--- Otrzymano odpowiedź 1 ---")
    print(odpowiedz_1[:150] + "...")  # Wyświetlenie fragmentu

    print("\nCzekam 20 sekund przed wysłaniem drugiego zapytania...")
    time.sleep(20)

    # Drugi prompt (przeglądarka nadal otwarta)
    odpowiedz_2 = bot.send_prompt("second test")
    print("\n--- Otrzymano odpowiedź 2 ---")
    print(odpowiedz_2)
