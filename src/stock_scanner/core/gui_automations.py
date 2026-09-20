import logging
import time

from playwright.sync_api import sync_playwright

from src.stock_scanner.core.paths import configure_environment

logger = logging.getLogger(__name__)

URL = "https://espiebi.pap.pl/"
INTERVAL_SECONDS = 5


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("Otwieranie strony...")
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        refresh_button = page.locator("#refreshHomeId a.refreshButton")
        refresh_button.wait_for(state="visible", timeout=10_000)

        counter = 1

        try:
            while True:
                print(f"\n[{time.strftime('%H:%M:%S')}] --- Cykl nr {counter} ---")

                refresh_button.click()

                page.wait_for_timeout(1000)

                refresh_time = page.locator("#refreshHomeId .refreshDateTime").inner_text().strip()
                print(f" SUCCESS: Kliknięto 'ODŚWIEŻ'. Czas danych na stronie: {refresh_time}")

                links = page.locator("a")
                messages = []
                found_refresh = False

                for i in range(links.count()):
                    text = links.nth(i).inner_text().strip()

                    if not text:
                        continue

                    if text == "ODŚWIEŻ":
                        found_refresh = True
                        continue

                    if found_refresh:
                        messages.append(text)

                    if len(messages) == 5:
                        break

                print("PIERWSZE 5 KOMUNIKATÓW:")
                for i, message in enumerate(messages, start=1):
                    print(f"  {i}. {message}")

                counter += 1

                print(f"Czekam {INTERVAL_SECONDS} sekund na następne odświeżenie...")
                page.wait_for_timeout(INTERVAL_SECONDS * 1000)

        except KeyboardInterrupt:
            print("\nZatrzymano pętlę na żądanie użytkownika.")

        finally:
            browser.close()


if __name__ == "__main__":
    configure_environment()
    main()
