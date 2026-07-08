import time
from typing import Optional, Tuple

import cv2
import mss
import numpy as np
import pyautogui
import pyperclip
from cv2.typing import MatLike


def get_screen_image() -> Tuple[MatLike, dict]:
    with mss.MSS() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)

        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    return img, monitor


def find_input(threshold: float = 0.85) -> Optional[Tuple[int, int, float]]:
    img, monitor = get_screen_image()

    template_path = "stock_scanner/assets/zapytaj.png"
    template = cv2.imread(template_path, cv2.IMREAD_COLOR)

    result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        h, w = template.shape[:2]

        x = max_loc[0] + w // 2 + monitor["left"]
        y = max_loc[1] + h // 2 + monitor["top"]

        return (x, y, max_val)
    else:
        print("Nie znaleziono pola inputu")
        return None


def paste_into_input(text: str = "some_text") -> None:
    input_point = find_input()

    if input_point is None:
        print("Nie można wkleić — brak inputa")
        return

    x, y, score = input_point
    pyperclip.copy(text)
    time.sleep(1)
    pyautogui.click(x, y)
    time.sleep(1)
    pyautogui.hotkey("ctrl", "v")


def scroll_to_bottom() -> None:
    input_point = find_input()

    if input_point is None:
        print("Nie można wkleić — brak inputa")
        return

    x, y, score = input_point
    empty_field = (x - 200, y)
    pyautogui.moveTo(empty_field, duration=1)
    pyautogui.click(empty_field)
    time.sleep(0.5)
    pyautogui.press("end")


def findlast_copy_icon(threshold: float = 0.85) -> Optional[Tuple[int, int]]:
    with mss.MSS() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)

        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    template_path = "stock_scanner/assets/copy_icon.png"
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

    bottom = max(centers, key=lambda p: p["y"])
    return (bottom["x"], bottom["y"])


if __name__ == "__main__":
    print("Start soon...")
    paste_into_input()
    time.sleep(0.5)
    scroll_to_bottom()
    time.sleep(1)
    copy_icon = findlast_copy_icon()
    pyautogui.moveTo(copy_icon, duration=0.5)
    time.sleep(1)
    pyautogui.click(copy_icon)


# ===================== SOME DEBUG FEARURES===============
# pyautogui.moveTo(center_x, center_y, duration=1)
# cv2.circle(img, (center_x, center_y), 5, (0, 0, 255), -1)
# pyautogui.moveTo(bottom["x"], bottom["y"], duration=2)
# pyautogui.click(bottom["x"], bottom["y"])
# cv2.imshow("DEBUG", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
