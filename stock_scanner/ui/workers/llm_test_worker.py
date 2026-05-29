import json

from google.genai import Client, types
from PySide6.QtCore import QThread, Signal

from stock_scanner.core.email_alerts import _load_config
from stock_scanner.download.config import email_config_path
from stock_scanner.download.database import get_connection


def _load_config() -> dict | None:
    if not email_config_path.exists():
        print(f"CONFIG NOT FOUND: {email_config_path}")
        return None

    try:
        with open(email_config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"CONFIG ERROR: {e}")
        return None


class GeminiWorker(QThread):
    response_received = Signal(str)
    config = _load_config()

    my_prompt = (
        "Wejdź w podany link. Przeanalizuj jego treść i oceń jego potencjał w kontekście wzrostu lub "
        "spadku danego instrumentu na giełdzie, którego dotyczy ten wpis. Jeśli są jakiekolwiek "
        "załączniki, otwórz każdy z nich oraz również je przeanalizuj w kontekście takim jak napisałem "
        "wcześniej. Jako odpowiedź zwrotną, masz do dyspozycji następujące opcje: Silny wzrost, "
        "Wzrost, Neutralny, Spadek, Silny spadek. Całą analizę wykonaj samodzielnie w oparciu o dane "
        "techniczne, opinie maklerów i innych profesjonalistów, strategie, prognozy i inne czynniki, "
        "które uznasz za istotne dla danej spółki/instrumentu. Analiza ma charakter wyłącznie "
        "edukacyjny/informacyjny i nie stanowi porady inwestycyjnej"
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

            entry = self._get_first_entry()
            title, link = entry
            prompt = self._build_prompt(title, link)

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

    def _build_prompt(self, title: str, link: str) -> str:
        prompt = f"{self.my_prompt}\n\nTytuł wpisu: {title}\nLink: {link}\n"
        return prompt

    def _get_first_entry(self) -> tuple[str, str] | None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT title, link FROM entries ORDER BY published DESC LIMIT 1")
            row = cur.fetchone()
            return None if row is None else (row[0], row[1])
        finally:
            conn.close()
