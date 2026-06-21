from google.genai import Client
from openai import OpenAI
from PySide6.QtCore import QThread, Signal

from stock_scanner.download.config import load_config

my_prompt = (
    "Przeanalizuj jego treść podanego tekstu i oceń jego potencjał "
    "w kontekście wzrostu lub spadku danego instrumentu na giełdzie, "
    "którego dotyczy ten wpis. Jako output oczekuję 2 rzeczy: instrumentu"
    "lub spółki, której artykuł dotyczy. Jeśli nie ma jasno sprecyzowanej"
    " informacji o instrumencie, wydedukuj z artykułu jaki instrument"
    " giełdowy może najmocniej zareagować na podany artykuł. Druga rzecz to"
    " chcę, abyś ocenił potencjał wzrostu lub spadku: Silny wzrost, Wzrost, Neutralny, Spadek, "
    "Silny spadek. Całą analizę wykonaj samodzielnie w oparciu o dane "
    "techniczne, opinie maklerów i innych profesjonalistów, strategie, "
    "prognozy i inne czynniki, które uznasz za istotne dla danej "
    "spółki/instrumentu. Analiza ma charakter wyłącznie edukacyjny/"
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
