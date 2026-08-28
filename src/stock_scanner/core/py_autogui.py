import logging
import time
from typing import Optional, Tuple

import cv2
import mss
import numpy as np
import pyautogui
import pyperclip

from src.stock_scanner.core.debug_screen import take_screenshot
from src.stock_scanner.core.paths import configure_environment, get_assets_dir
from src.stock_scanner.core.utils import get_actual_time

logger = logging.getLogger(__name__)


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
        logger.error(f"{get_actual_time()} Automation error - Input template not found")
        return None

    result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape[:2]

        x = max_loc[0] + w // 2 + monitor["left"]
        y = max_loc[1] + h // 2 + monitor["top"]

        return (x + 200, y)
    else:
        logger.error(f"{get_actual_time()} Automation error - Input field not found")
        return None


def paste_into_input(text: str) -> None:
    input_point = find_input()

    if input_point is None:
        logger.error(f"{get_actual_time()} Automation error: Cant paste - input not found")
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
        logger.error(f"{get_actual_time()} Automation error - Cant scroll - Input not found")
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
    # print(f"Copy icon path: {template_path}")
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template is None:
        logger.error(f"{get_actual_time()} Automation error - copy icon not found")
        take_screenshot("copy_not_found.png")
        return None

    h, w = template.shape[:2]

    result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)

    locations = np.where(result >= threshold)

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
    configure_environment()
