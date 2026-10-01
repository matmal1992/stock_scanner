from pathlib import Path

import cv2
import mss
import numpy as np
import pyautogui

DEBUG_DIR = Path("debug")


def take_screenshot(filename: str = "screen.png") -> None:
    DEBUG_DIR.mkdir(exist_ok=True)

    with mss.MSS() as sct:
        monitor = sct.monitors[0]
        screenshot = sct.grab(monitor)

        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    path = DEBUG_DIR / filename
    cv2.imwrite(str(path), img)

    # print(f"Screenshot saved: {path}")


def show_detected(img: np.ndarray, points: list[tuple[int, int]]) -> np.ndarray:
    debug_img = img.copy()

    for x, y in points:
        cv2.circle(debug_img, (x, y), 5, (0, 255, 0), -1)

    DEBUG_DIR.mkdir(exist_ok=True)

    path = DEBUG_DIR / "detected.png"
    cv2.imwrite(str(path), debug_img)

    return debug_img


def show_mouse(img: np.ndarray) -> np.ndarray:
    debug_img = img.copy()

    x, y = pyautogui.position()

    cv2.circle(debug_img, (x, y), 5, (0, 255, 255), -1)

    DEBUG_DIR.mkdir(exist_ok=True)

    path = DEBUG_DIR / "clicked.png"
    cv2.imwrite(str(path), debug_img)

    return debug_img
