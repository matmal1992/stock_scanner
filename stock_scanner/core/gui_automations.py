import pyautogui

def click_image(path: str, confidence: float = 0.8) -> bool:
    location = pyautogui.locateOnScreen(path, confidence=confidence)

    if location:
        x, y = pyautogui.center(location)
        pyautogui.click(x, y)
        print(f"Kliknięto: {path} -> ({x}, {y})")
        return True

    print(f"Nie znaleziono: {path}")
    return False