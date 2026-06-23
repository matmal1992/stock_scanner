from time import time

from google.genai import Client
from openai import OpenAI
from PySide6.QtCore import QThread, Signal

from stock_scanner.download.config import load_config

my_prompt = (
    "Przeanalizuj zawartość podanego linku i oceń jego potencjał "
    "w kontekście wzrostu lub spadku danego instrumentu na giełdzie, "
    "którego dotyczy ten link. Jako output oczekuję 2 rzeczy: instrumentu"
    "lub spółki, której artykuł dotyczy. Jeśli nie ma jasno sprecyzowanej"
    " informacji o instrumencie, wydedukuj z artykułu jaki instrument"
    " giełdowy może najmocniej zareagować na podany artykuł. Druga rzecz to"
    "ocena potencjału wzrostu lub spadku: Silny wzrost, Wzrost, Neutralny, Spadek, "
    "Silny spadek. Całą analizę wykonaj samodzielnie w oparciu o dane "
    "techniczne, opinie maklerów i innych profesjonalistów, strategie, "
    "prognozy i inne czynniki, które uznasz za istotne dla danej "
    "spółki/instrumentu. A więc, oczekuję odpowiedzi złożonej z maksymalnie "
    " czterech słów. Na przykład Creotech Instruments (może być też symbol "
    "giełdowy CRI), Silny wzrost. Ta analiza ma charakter wyłącznie edukacyjny/"
    "informacyjny i nie stanowi porady inwestycyjnej."
)


class GeminiWorker(QThread):
    response_received = Signal(str)

    def __init__(self, article_text: str) -> None:
        super().__init__()
        self.article_text = article_text
        self.config = load_config()
        self.prompt = my_prompt

    def run(self) -> None:
        try:
            client = Client(api_key=self.config.get("gemini_api_key"))

            prompt = self.build_prompt()

            response = client.models.generate_content(
                # model='gemini-2.5-flash',
                # model='gemini-2.5-pro', docelowy, do sprawdzenia
                model="gemini-2.0-flash",
                contents=prompt,
            )

            self.response_received.emit(response.text)

        except Exception as e:
            self.response_received.emit(f"Błąd połączenia: {str(e)}")

    def build_prompt(self) -> str:
        prompt = f"{my_prompt}\n\nTreść artykułu: {self.article_text}"
        return prompt


from PySide6.QtCore import QThread, Signal


class GPTWorker(QThread):
    response_received = Signal(str)

    def __init__(self, article_text: str) -> None:
        super().__init__()
        self.article_text = article_text
        self.config = load_config()
        self.prompt = my_prompt

    def run(self) -> None:
        try:
            client = OpenAI(api_key=self.config.get("openai_api_key"))

            prompt = self.build_prompt()

            response = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
            )

            output_text = response.output_text

            self.response_received.emit(output_text)

        except Exception as e:
            self.response_received.emit(f"Błąd połączenia: {str(e)}")

    def build_prompt(self) -> str:
        return f"{my_prompt}\n\nTreść artykułu:\n{self.article_text}"


import time

import pyautogui
import pyperclip


class ManualPromptWorker(QThread):
    response_received = Signal(str)
    input_box = (650, 950)
    send_button = (1325, 950)
    cancel_point = (1325, 890)
    copy_point = (595, 440)
    empty_field = (400, 950)
    link_to_read: str

    def __init__(self, link: str) -> None:
        super().__init__()
        self.link_to_read = link

    def send_prompt(self, prompt: str) -> None:
        print("sending prompt")
        # klik w input
        # pyautogui.click(INPUT_BOX)
        self.click_debug(self.input_box[0], self.input_box[1], "INPUT_BOX")
        time.sleep(0.5)

        # wpisz prompt
        pyautogui.write(prompt, interval=0.02)

        # wyślij
        pyautogui.press("enter")

    def get_response(self):
        time.sleep(15)  # czekaj aż model odpowie (możesz poprawić później)
        pyautogui.press("end")
        pyautogui.click(self.cancel_point)
        pyautogui.click(self.copy_point)
        pyautogui.click()

        # zaznacz wszystko od odpowiedzi
        # print("Zaznaczenie przez dragging")
        # select_response()
        # time.sleep(5)

        # print("Kopiowanie Ctrl + c")
        # pyautogui.hotkey("ctrl", "c")
        # time.sleep(5)

        print("Wklejanie Ctrl + v")
        return pyperclip.paste()

    def click_debug(self, x, y, label="") -> None:
        print(f"Klik: {label} -> ({x}, {y})")

        # ruch kursora (wizualny debug)
        pyautogui.moveTo(x, y, duration=0.3)

        # małe „mrugnięcie”
        pyautogui.click()
        time.sleep(0.2)

    def build_prompt(self) -> str:
        return f"{my_prompt}\n\nLink:\n{self.link_to_read}"

    def run(self) -> None:
        print("Worker started")

        prompt = self.build_prompt()

        self.send_prompt(prompt)
        response = self.get_response()

        self.response_received.emit(response)

        print("RESPONSE:\n", response)

    # def select_response(self) -> None:
    #     pyautogui.press("end")
    #     # x, y, w, h = RESPONSE_REGION
    #     # img = pyautogui.screenshot(region=(x, y, w, h))
    #     # img.save("region_test.png")

    #     # pyautogui.moveTo(x, y, duration=0.5)
    #     pyautogui.click(self.empty_field)
    #     # pyautogui.mouseDown()

    #     # przeciągnij przez cały obszar odpowiedzi
    #     # pyautogui.moveTo(x + w, y + h, duration=0.5)

    #     # pyautogui.mouseUp()

    #     # === TEST ===
    #     prompt = self.build_prompt()

    #     self.send_prompt(prompt)
    #     response = self.get_response()
    #     self.response_received.emit(response)

    #     print("RESPONSE:\n", response)
