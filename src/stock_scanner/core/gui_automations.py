import time
from pathlib import Path
from typing import Optional, Tuple

import cv2
import mss
import numpy as np
import pyautogui
import pyperclip
from playwright.sync_api import Page, sync_playwright

from src.stock_scanner.core.debug_screen import take_screenshot
from src.stock_scanner.core.paths import configure_environment, get_assets_dir
from src.stock_scanner.strategies.news_tracker.entry_repo import NewsEntry


def get_news(output_dir: Optional[Path] = None) -> list[NewsEntry]:
    """Scrape Bankier news without starting the worker or using the database."""
    configure_environment()
    screenshot_dir = output_dir or Path.cwd() / "debug_news"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    url = "https://www.bankier.pl/gielda/wiadomosci"
    item_selector = "li.m-listing-article-list__item"

    def screenshot(page: Page, name: str) -> None:
        page.screenshot(path=screenshot_dir / f"{name}.png", full_page=True)

    entries: list[NewsEntry] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            screenshot(page, "01_before_navigation")
            page.goto(url, timeout=30_000, wait_until="domcontentloaded")
            screenshot(page, "02_after_navigation")

            cookie_button = page.locator("button:has-text('Zaakceptuj i zamknij')").first
            if cookie_button.count() > 0 and cookie_button.is_visible(timeout=2_000):
                screenshot(page, "03_cookie_banner_before_click")
                cookie_button.click()
                page.wait_for_timeout(1_000)
                screenshot(page, "04_after_cookie_click")
            else:
                screenshot(page, "03_no_cookie_banner")

            screenshot(page, "05_page_validation")
            page.wait_for_selector(item_selector, timeout=15_000)
            items = page.locator(item_selector)
            screenshot(page, "06_news_list_found")

            for index in range(min(items.count(), 5)):
                item = items.nth(index)
                item.screenshot(path=screenshot_dir / f"07_item_{index}.png")

                anchor = item.locator("a.m-listing-article-list__anchor")
                if anchor.count() == 0:
                    screenshot(page, f"08_item_{index}_invalid")
                    continue

                link = anchor.get_attribute("href")
                title = item.locator(".m-listing-article-list__title").inner_text().strip()
                published = item.locator(".m-listing-article-list__date-time").inner_text().strip()

                if not link or not title:
                    screenshot(page, f"08_item_{index}_invalid")
                    continue

                if link.startswith("/"):
                    link = "https://www.bankier.pl" + link

                entries.append(
                    {
                        "id": 0,
                        "title": title,
                        "link": link,
                        "published": published,
                        "source_type": "NEWS",
                        "ticker": None,
                        "llm": "pending",
                        "sentiment": "-",
                    }
                )

            screenshot(page, "09_scraping_finished")
        except Exception:
            screenshot(page, "error_last_page_state")
            raise
        finally:
            browser.close()

    return entries


def get_screen_image() -> Tuple[np.ndarray, dict]:
    with mss.MSS() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)

        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    return img, monitor


def find_input(threshold: float = 0.85) -> Optional[Tuple[int, int]]:
    img, monitor = get_screen_image()

    template_path = get_assets_dir() / "input_icon.png"
    # print(f"Input icon path: {template_path}")
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    if template is None:
        print("\nTemplate not found")
        # raise ValueError("Template not found")
        return None

    result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape[:2]

        x = max_loc[0] + w // 2 + monitor["left"]
        y = max_loc[1] + h // 2 + monitor["top"]

        return (x + 200, y)
    else:
        print("Nie znaleziono pola inputu")
        return None


def paste_into_input(text: str) -> None:
    input_point = find_input()

    if input_point is None:
        print("Nie można wkleić — brak inputa")
        take_screenshot("no_input_found.png")
        return

    x, y = input_point
    pyperclip.copy(text)
    time.sleep(1)
    pyautogui.click(x, y)
    time.sleep(1)
    pyautogui.hotkey("ctrl", "v")


def scroll_to_bottom() -> None:
    input_point = find_input()

    if input_point is None:
        print("Nie można wkleić — brak inputa")
        take_screenshot("no_input_point_found.png")
        # dodać debugowanie w postaci zrzutu z ekranu + zapis do pliku z zaznaczonym obszarem
        return

    x, y = input_point
    empty_field = (x - 300, y)
    pyautogui.moveTo(empty_field, duration=1)
    pyautogui.click(empty_field)
    time.sleep(0.5)
    pyautogui.press("end")


def find_last_copy_icon(threshold: float = 0.85) -> Optional[Tuple[int, int]]:
    with mss.MSS() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)

        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    template_path = get_assets_dir() / "copy_icon.png"
    print(f"Copy icon path: {template_path}")
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        print("\nTemplate not found")
        take_screenshot("copy_not_found.png")
        # raise ValueError("Template not found")
        return None

    h, w = template.shape[:2]

    result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)

    locations = np.where(result >= threshold)

    print(f"Znaleziono {len(locations[0])} dopasowań copy icon")

    centers = []

    for pt in zip(*locations[::-1]):
        x, y = pt

        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        center_x = x + w // 2 + monitor["left"]
        center_y = y + h // 2 + monitor["top"]
        centers.append((center_x, center_y))

    # if debug:
    # show_detected(img, centers)

    bottom = max(centers, key=lambda p: p[1])
    return bottom


def test_autogui() -> None:
    print("Start soon...")
    paste_into_input("some_text")
    time.sleep(0.5)
    scroll_to_bottom()
    time.sleep(1)
    copy_icon = find_last_copy_icon()
    pyautogui.moveTo(copy_icon, duration=0.5)
    time.sleep(1)
    pyautogui.click(copy_icon)
    print("LLM ended")
    # todo: zwracaj odpowiednie sygnały/komunikaty w zależności co się wysypało


if __name__ == "__main__":
    news = get_news()
    print(f"Zescrapowano wiadomości: {len(news)}")
    for entry in news:
        print(f"{entry['published']} | {entry['title']} | {entry['link']}")
