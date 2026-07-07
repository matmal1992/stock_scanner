import time
from typing import Optional, Tuple

import cv2
import mss
import mss.tools
import numpy as np
import pyautogui


def find_icon(template_path: str, threshold: float = 0.85) -> Optional[Tuple[int, int, float]]:
    with mss.MSS() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)

        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape[:2]

        x = max_loc[0] + w // 2 + monitor["left"]
        y = max_loc[1] + h // 2 + monitor["top"]

        return (x, y, max_val)

    return None


def click_icon_and_scroll(template_path: str, threshold: float = 0.85) -> Optional[Tuple[int, int]]:
    result = find_icon(template_path, threshold)

    if not result:
        print("Nie znaleziono ikony")
        return None

    x, y, score = result
    original_point = (x, y)
    pyautogui.click(x, y)
    print(f"Kliknięto ikonę: ({x}, {y}) score={score}")
    time.sleep(1)
    pyautogui.click(x - 200, y)
    print("Kliknięto ikonę: w wolne pole")

    time.sleep(0.5)
    pyautogui.press("end")
    print("Komenda scroll wykonana")

    return original_point


def find_and_click_last_copy_icon(template_path: str, threshold: float = 0.85) -> None:
    with mss.MSS() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)

        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    template = cv2.imread(template_path, cv2.IMREAD_COLOR)
    h, w = template.shape[:2]

    result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)

    locations = np.where(result >= threshold)

    print(f"Znaleziono {len(locations[0])} dopasowań")

    centers = []

    for pt in zip(*locations[::-1]):
        x, y = pt

        cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        center_x = x + w // 2
        center_y = y + h // 2
        centers.append({"x": center_x, "y": center_y})
        pyautogui.moveTo(center_x, center_y, duration=1)
        cv2.circle(img, (center_x, center_y), 5, (0, 0, 255), -1)

    bottom = max(centers, key=lambda p: p["y"])
    pyautogui.moveTo(bottom["x"], bottom["y"], duration=2)
    pyautogui.click(bottom["x"], bottom["y"])

    cv2.imshow("DEBUG", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    print("Start soon...")
    time.sleep(1)
    click_icon_and_scroll("stock_scanner/assets/ask_anything.png")
    time.sleep(1)
    find_and_click_last_copy_icon("stock_scanner/assets/copy_icon.png")
