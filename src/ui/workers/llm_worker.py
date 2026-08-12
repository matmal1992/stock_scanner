import time

import pyautogui
import pyperclip
from PySide6.QtCore import QObject, QThread, Signal

from src.core.debug_screen import show_mouse, take_screenshot
from src.core.gui_automations import (
    find_last_copy_icon,
    paste_into_input,
    scroll_to_bottom,
)

my_prompt = (
    "Przeanalizuj zawartość podanego linku i oceń jego potencjał "
    "w kontekście wzrostu lub spadku danego instrumentu na giełdzie, "
    "którego dotyczy ten link. Jako output oczekuję: instrumentu"
    "lub spółka, której artykuł dotyczy. Jeśli nie ma jasno sprecyzowanej"
    " informacji o instrumencie, wydedukuj z artykułu jaki instrument"
    " giełdowy może najmocniej zareagować na podany artykuł. Druga rzecz to"
    "ocena potencjału wzrostu lub spadku: Silny wzrost, Wzrost, Neutralny, Spadek, "
    "Silny spadek. Całą analizę wykonaj samodzielnie w oparciu o dane "
    "techniczne, opinie maklerów i innych profesjonalistów, strategie, "
    "prognozy i inne czynniki, które uznasz za istotne dla danej "
    "spółki/instrumentu. A więc, oczekuję odpowiedzi dokładnie w takim formacie: "
    " Nazwa instrumentu: [pełna nazwa instrumentu], Symbol instrumentu: [symbol giełdowy],"
    "Prognoza: [Silny spadek, Spadek, Neutralny, Wzrost, Silny wzrost]. "
    "Oczekuję samego tekstu, bez źródeł i odnośników."
    "Ta analiza ma charakter wyłącznie edukacyjny/"
    "informacyjny i nie stanowi porady inwestycyjnej."
)


class ManualPromptWorker(QObject):
    response_received = Signal(int, str)
    error = Signal(str)
    link_to_read: str
    entry_id: int

    def __init__(self, link: str, entry_id: int) -> None:
        super().__init__()
        self.link_to_read = link
        self.entry_id = entry_id

    def build_prompt(self) -> str:
        return f"{my_prompt} Link do analizy: {self.link_to_read}"

    def run(self) -> None:
        try:
            prompt = self.build_prompt()
            scroll_to_bottom()
            time.sleep(0.5)
            paste_into_input(prompt)
            time.sleep(0.5)
            pyautogui.press("enter")
            time.sleep(15)
            scroll_to_bottom()
            copy_icon = find_last_copy_icon()

            img = take_screenshot("before_click.png")

            pyautogui.moveTo(copy_icon, duration=0.5)
            show_mouse(img)
            time.sleep(1)
            pyautogui.click(copy_icon)

            response = pyperclip.paste()
            self.response_received.emit(self.entry_id, response)
            print("RESPONSE:\n", response)

        except Exception as exc:
            message = f"LLM worker error: {exc}"
            print(message)
            self.error.emit(message)


class LLMService(QObject):
    result = Signal(int, str)

    def run(self, link: str, entry_id: int) -> None:
        thread = QThread()
        self.worker = ManualPromptWorker(link, entry_id)
        self.worker.moveToThread(thread)
        self.worker.response_received.connect(self.result)
        self.worker.response_received.connect(thread.quit)
        self.worker.response_received.connect(self.worker.deleteLater)
        self.worker.error.connect(thread.quit)
        self.worker.error.connect(self.worker.deleteLater)
        thread.started.connect(self.worker.run)
        thread.finished.connect(thread.deleteLater)
        thread.start()
