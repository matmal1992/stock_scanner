import json
import urllib.error
import urllib.request
from typing import Any

from PySide6.QtCore import QObject, Signal

from stock_scanner.download.config import email_config_path
from stock_scanner.download.database import get_connection

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-3.5-turbo"

PROMPT_TEMPLATE = (
    "Wejdź w podany link. Przeanalizuj jego treść i oceń jego potencjał w kontekście wzrostu lub "
    "spadku danego instrumentu na giełdzie, którego dotyczy ten wpis. Jeśli są jakiekolwiek "
    "załączniki, otwórz każdy z nich oraz również je przeanalizuj w kontekście takim jak napisałem "
    "wcześniej. Jako odpowiedź zwrotną, masz do dyspozycji następujące opcje: Silny wzrost, "
    "Wzrost, Neutralny, Spadek, Silny spadek. Całą analizę wykonaj samodzielnie w oparciu o dane "
    "techniczne, opinie maklerów i innych profesjonalistów, strategie, prognozy i inne czynniki, "
    "które uznasz za istotne dla danej spółki/instrumentu."
)


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


class LLMTestWorker(QObject):
    finished = Signal()
    error = Signal(str)
    result = Signal(str)
    log = Signal(str)
    config = _load_config()

    def run(self) -> None:
        try:
            self.log.emit("Rozpoczynam test LLM...")
            entry = self._get_first_entry()
            if entry is None:
                raise RuntimeError("Brak wpisów w bazie rss.db. Załaduj najpierw RSS.")

            title, link = entry
            prompt = self._build_prompt(title, link)
            response = self._call_openai(prompt)
            self.result.emit(response)
        except Exception as exc:
            self.error.emit(str(exc))
        finally:
            self.finished.emit()

    def _get_first_entry(self) -> tuple[str, str] | None:
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT title, link FROM entries ORDER BY published DESC LIMIT 1")
            row = cur.fetchone()
            return None if row is None else (row[0], row[1])
        finally:
            conn.close()

    def _build_prompt(self, title: str, link: str) -> str:
        prompt = f"{PROMPT_TEMPLATE}\n\nTytuł wpisu: {title}\nLink: {link}\n"
        return prompt

    def _call_openai(self, prompt: str) -> str:
        api_key = self.config.get("openai_api_key")
        if not api_key:
            raise RuntimeError(
                "Brak klucza OPENAI_API_KEY w środowisku. Ustaw zmienną środowiskową i spróbuj ponownie."
            )

        request_data = json.dumps(
            {
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 1000,
            }
        ).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        request = urllib.request.Request(
            OPENAI_API_URL,
            data=request_data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_text = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Błąd OpenAI API: {exc.code} {exc.reason}. Odpowiedź: {error_text}")
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Błąd sieciowy podczas łączenia z OpenAI: {exc.reason}")

        data = json.loads(raw)
        return self._parse_response(data)

    def _parse_response(self, data: Any) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("Brak odpowiedzi od ChatGPT.")

        message = choices[0].get("message", {})
        content = message.get("content", "").strip()
        if not content:
            raise RuntimeError("Otrzymano pustą odpowiedź od ChatGPT.")

        return content
