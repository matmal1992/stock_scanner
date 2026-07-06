import time
from typing import Optional, Tuple

import cv2
import mss
import mss.tools
import numpy as np
import pyautogui


def find_icon(template_path: str, threshold: float = 0.85) -> Optional[Tuple[int, int, float]]:
    with mss.MSS() as sct:
        monitor = sct.monitors[0]  # wszystkie monitory
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


def click_icon(template_path: str, threshold: float = 0.85) -> bool:
    result = find_icon(template_path, threshold)

    if result:
        x, y, score = result
        pyautogui.click(x, y)
        print(f"Kliknięto ikonę: ({x}, {y}) score={score}")
        return True

    print("Nie znaleziono ikony")
    return False


if __name__ == "__main__":
    import time

    print("Start za 3 sekundy...")
    time.sleep(3)

    click_icon("stock_scanner/assets/zapytaj.png")
