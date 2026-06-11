from google.genai import Client, types
from PySide6.QtCore import QThread, Signal

from stock_scanner.download.config import load_config
from stock_scanner.download.database_useless import get_first_entry


class GeminiWorker(QThread):
    response_received = Signal(str)
    config = load_config()

    my_prompt = (
        "Wejdź w podany link. Przeanalizuj jego treść i oceń jego potencjał "
        "w kontekście wzrostu lub spadku danego instrumentu na giełdzie, "
        "którego dotyczy ten wpis. Jeśli są jakiekolwiek załączniki, otwórz "
        "każdy z nich oraz również je przeanalizuj w kontekście takim jak "
        "napisałem wcześniej. Jako odpowiedź zwrotną masz do dyspozycji "
        "następujące opcje: Silny wzrost, Wzrost, Neutralny, Spadek, "
        "Silny spadek. Całą analizę wykonaj samodzielnie w oparciu o dane "
        "techniczne, opinie maklerów i innych profesjonalistów, strategie, "
        "prognozy i inne czynniki, które uznasz za istotne dla danej "
        "spółki/instrumentu. Analiza ma charakter wyłącznie edukacyjny/"
        "informacyjny i nie stanowi porady inwestycyjnej."
    )

    def __init__(self) -> None:
        super().__init__()
        self.prompt = self.my_prompt

    def run(self) -> None:
        try:
            client = Client(api_key=self.config.get("gemini_api_key"))
            config = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )

            title, link = get_first_entry()
            prompt = self.build_prompt(title, link)

            response = client.models.generate_content(
                # model='gemini-2.5-flash',
                # model='gemini-2.5-pro', docelowy, do sprawdzenia
                model="gemini-2.0-flash",
                contents=prompt,
                config=config,
            )
            self.response_received.emit(response.text)
        except Exception as e:
            self.response_received.emit(f"Błąd połączenia: {str(e)}")

    def build_prompt(self, title: str, link: str) -> str:
        prompt = f"{self.my_prompt}\n\nTytuł wpisu: {title}\nLink: {link}\n"
        return prompt
