import json
import logging
import time
from typing import Any, cast

import pyautogui
import pyperclip
from PySide6.QtCore import QObject, QThread, Signal

from src.stock_scanner.core.gpt_prompter import GPTPrompter
from src.stock_scanner.core.py_autogui import find_last_copy_icon, paste_into_input, scroll_to_bottom
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, LLMResponse, NewsEntry

logger = logging.getLogger(__name__)

my_prompt = """WYKONAJ PONIŻSZE POLECENIE DOSŁOWNIE.

Otwórz i przeanalizuj rzeczywistą treść artykułu znajdującego się pod podanym linkiem.
Nie zgaduj treści na podstawie samego tytułu ani adresu URL.

KROK 1 — IDENTYFIKACJA SPÓŁKI

Ustal, czy artykuł dotyczy bezpośrednio konkretnej spółki, której akcje są notowane na giełdzie.

Za „dotyczy bezpośrednio” uznaj wyłącznie artykuł, którego głównym przedmiotem jest konkretna spółka, 
jej działalność, wyniki, zarząd, inwestycje, produkty, prognozy, 
komunikaty lub inne zdarzenia bezpośrednio związane z tą spółką.

NIE WOLNO identyfikować spółki na podstawie potencjalnego pośredniego wpływu artykułu.

Odrzuć artykuły dotyczące wyłącznie:

- indeksów,
- surowców,
- walut,
- obligacji,
- stóp procentowych,
- gospodarki,
- całych sektorów,
- krajów,
- rynków jako całości,
- trendów giełdowych,
- innych instrumentów niż konkretnej spółki.

Przykład:
Jeżeli artykuł dotyczy wzrostu ceny miedzi, nie identyfikuj KGHM tylko dlatego, 
że cena miedzi może wpływać na wyniki KGHM.

Jeżeli artykuł dotyczy sytuacji na rynku ropy, 
nie identyfikuj spółki naftowej tylko dlatego, że może ona na tym skorzystać lub stracić.

Jeżeli artykuł dotyczy konkretnej spółki i jednocześnie opisuje wpływ cen surowców, 
kursów walut lub sytuacji rynkowej na tę spółkę, traktuj go jako artykuł dotyczący tej spółki.

Jeżeli artykuł nie dotyczy bezpośrednio konkretnej, notowanej na giełdzie spółki, ustaw:

"relevant": false

oraz:

"company": null
"ticker": null
"forecast": null
"sector": "other"

KROK 2 — IDENTYFIKACJA SPÓŁKI

Jeżeli artykuł dotyczy bezpośrednio konkretnej spółki giełdowej:

- podaj jej rzeczywistą, pełną nazwę,
- podaj rzeczywisty symbol giełdowy (ticker),
- nie wymyślaj symbolu,
- nie używaj nazwy indeksu, surowca, waluty ani innego instrumentu jako nazwy spółki.

Jeżeli artykuł dotyczy kilku spółek, wybierz tę spółkę, 
której artykuł dotyczy najbardziej bezpośrednio 
i której kurs powinien być najbardziej wrażliwy na przedstawioną informację.

KROK 3 — KLASYFIKACJA SEKTORA

Ustal, czy spółka lub główny temat artykułu należy do jednego z poniższych sektorów:

- "zbrojeniowy"
- "dronowy"
- "medyczny"
- "hi-tech"
- "kosmiczny"
- "other"

Pole "sector" musi przyjąć dokładnie jedną z powyższych wartości.

Klasyfikację wykonuj na podstawie rzeczywistej działalności spółki 
oraz głównego tematu artykułu.

Nie przypisuj sektora wyłącznie na podstawie odległego lub 
potencjalnego zastosowania produktu.

Jeżeli spółka lub główny temat artykułu nie pasuje jednoznacznie 
do żadnego z pięciu wymienionych sektorów, ustaw:

"sector": "other"

Jeżeli spółka działa w kilku sektorach, 
wybierz sektor najbardziej związany z tematyką konkretnego artykułu.

Przykłady:

- producent broni, amunicji, systemów rakietowych lub technologii wojskowych → "zbrojeniowy"
- producent dronów lub technologii bezzałogowych → "dronowy"
- producent leków, urządzeń medycznych lub świadczący usługi medyczne → "medyczny"
- spółka zajmująca się zaawansowanymi technologiami, sztuczną inteligencją, elektroniką, 
oprogramowaniem lub innymi technologiami high-tech → "hi-tech"
- spółka zajmująca się technologiami kosmicznymi, satelitami, 
rakietami lub infrastrukturą kosmiczną → "kosmiczny"
- jeżeli żaden z powyższych przypadków nie pasuje → "other"

KROK 4 — PROGNOZA

Jeżeli artykuł dotyczy bezpośrednio konkretnej spółki giełdowej, 
oceń prawdopodobny wpływ informacji na kurs jej akcji.

Uwzględnij przede wszystkim informacje zawarte w artykule, 
a dodatkowo — jeżeli są dostępne — aktualne wyniki finansowe, dane techniczne, 
rekomendacje analityków, prognozy, strategię spółki i inne istotne aktualne informacje.

Bazuj wyłącznie na najnowszych dostępnych danych w odniesieniu do 
daty i godziny wykonania niniejszego polecenia.

Prognoza może przyjąć wyłącznie jedną z pięciu wartości:

- "Silny spadek"
- "Spadek"
- "Neutralny"
- "Wzrost"
- "Silny wzrost"

KROK 5 — FORMAT ODPOWIEDZI

Odpowiedź MUSI być poprawnym składniowo obiektem JSON.

Jeżeli artykuł NIE DOTYCZY konkretnej spółki giełdowej, zwróć dokładnie:

{
  "relevant": false,
  "company": null,
  "ticker": null,
  "forecast": null,
  "sector": "other"
}

Jeżeli artykuł DOTYCZY konkretnej spółki giełdowej, zwróć:

{
  "relevant": true,
  "company": "rzeczywista pełna nazwa spółki",
  "ticker": "rzeczywisty symbol giełdowy",
  "forecast": "jedna z pięciu dozwolonych wartości",
  "sector": "jedna z sześciu dozwolonych wartości"
}

KROK 6 — WALIDACJA

Przed wysłaniem odpowiedzi sprawdź:

1. Czy rzeczywiście otworzyłeś i przeanalizowałeś wskazany link.
2. Czy spółka jest konkretną spółką giełdową.
3. Czy artykuł dotyczy jej bezpośrednio, a nie tylko pośrednio.
4. Czy nie zakwalifikowałeś indeksu, surowca, waluty, obligacji, sektora lub rynku jako spółki.
5. Czy nazwa spółki jest rzeczywistą pełną nazwą.
6. Czy ticker jest rzeczywistym symbolem giełdowym.
7. Czy prognoza jest dokładnie jedną z pięciu dozwolonych wartości.
8. Czy sector jest dokładnie jedną z sześciu dozwolonych wartości.
9. Jeżeli "relevant" = false, czy company, ticker i forecast mają wartość null.
10. Jeżeli "relevant" = false, czy sector ma wartość "other".
11. Czy odpowiedź jest poprawnym JSON-em.
12. Czy odpowiedź nie zawiera żadnego tekstu poza obiektem JSON.

WAŻNE:

- Nie dodawaj komentarzy.
- Nie dodawaj uzasadnienia.
- Nie dodawaj źródeł.
- Nie dodawaj linków.
- Nie dodawaj Markdown.
- Nie używaj bloków ```json.
- Nie dodawaj tekstu przed ani po obiekcie JSON.
- Nie zwracaj placeholderów.
- Nie zwracaj dodatkowych pól, których nie określono w tym poleceniu.

OSTATECZNA ODPOWIEDŹ MUSI ZAWIERAĆ WYŁĄCZNIE POPRAWNY OBIEKT JSON.
"""

#     "Analiza ma charakter wyłącznie edukacyjny/informacyjny "
#     "i nie stanowi porady inwestycyjnej."


class ManualPromptWorker(QObject):
    def run(self, link: str) -> LLMResponse:
        try:
            prompt = f"{my_prompt} Link: {link}"
            scroll_to_bottom()
            time.sleep(0.5)
            paste_into_input(prompt)
            time.sleep(0.5)
            pyautogui.press("enter")
            time.sleep(15)
            scroll_to_bottom()
            copy_icon = find_last_copy_icon()

            # img = take_screenshot("before_click.png")

            pyautogui.moveTo(copy_icon, duration=0.5)
            # show_mouse(img)
            time.sleep(1)
            pyautogui.click(copy_icon)

            response = pyperclip.paste()
            return self._parse_response(response)

        except Exception as exc:
            logger.error(f"LLM worker error: {exc}")
            raise

    @staticmethod
    def _parse_response(response: str) -> LLMResponse:
        response = response.strip()

        if not response:
            raise ValueError("LLM zwrócił pustą odpowiedź")

        parsed: Any = json.loads(response)

        if not isinstance(parsed, dict):
            raise ValueError("Odpowiedź LLM nie jest obiektem JSON")

        required_fields = {"relevant", "company", "ticker", "forecast", "sector"}
        if set(parsed) != required_fields:
            raise ValueError("Odpowiedź LLM ma nieprawidłowe pola")

        allowed_forecasts = {
            "Silny spadek",
            "Spadek",
            "Neutralny",
            "Wzrost",
            "Silny wzrost",
        }
        allowed_sectors = {
            "zbrojeniowy",
            "dronowy",
            "medyczny",
            "hi-tech",
            "kosmiczny",
            "other",
        }

        if not isinstance(parsed["relevant"], bool):
            raise ValueError("Pole relevant musi być typu boolean")
        if parsed["sector"] not in allowed_sectors:
            raise ValueError("Nieprawidłowa wartość pola sector")

        if parsed["relevant"]:
            if not isinstance(parsed["company"], str) or not parsed["company"].strip():
                raise ValueError("Pole company musi zawierać nazwę spółki")
            if not isinstance(parsed["ticker"], str) or not parsed["ticker"].strip():
                raise ValueError("Pole ticker musi zawierać symbol spółki")
            if parsed["forecast"] not in allowed_forecasts:
                raise ValueError("Nieprawidłowa wartość pola forecast")
        elif parsed["company"] is not None or parsed["ticker"] is not None:
            raise ValueError("Dla relevant=false company i ticker muszą być null")
        elif parsed["forecast"] is not None or parsed["sector"] != "other":
            raise ValueError("Dla relevant=false forecast musi być null, a sector musi być other")

        return cast(LLMResponse, parsed)


class LLMService(QObject):
    log = Signal(str)
    error = Signal(str)
    finished = Signal()
    result = Signal(NewsEntry)

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.entry_repo = entry_repo

        self._thread: QThread | None = None
        self.worker: LLMQueueWorker | None = None

    def start(self) -> bool:
        if self._thread is not None and self._thread.isRunning():
            self.log.emit("LLM już działa")
            return False

        self._thread = QThread()

        self.worker = LLMQueueWorker(self.entry_repo)
        self.worker.moveToThread(self._thread)
        self.worker.log.connect(self.log)
        self.worker.error.connect(self.error)
        self.worker.finished.connect(self._thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.result.connect(self.result)

        self._thread.started.connect(self.worker.run)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()

        return True

    def stop(self) -> None:
        if self.worker is not None:
            self.worker.stop()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def _on_thread_finished(self) -> None:
        self._thread = None
        self.worker = None

        self.finished.emit()


class LLMQueueWorker(QObject):
    finished = Signal()
    error = Signal(str)
    log = Signal(str)
    result = Signal(object)

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self.running = True
        self.prompt_worker = ManualPromptWorker()

    def stop(self) -> None:
        self.running = False

    def run(self) -> None:
        self.log.emit("LLM queue started")
        prompter: GPTPrompter | None = None
        entry_count: int = 0

        try:
            self.log.emit("Uruchamianie przeglądarki ChatGPT...")
            prompter = GPTPrompter(headless=True)
            prompter.start()

            while self.running:
                pending = self.entry_repo.get_last_pending()

                if pending is None:
                    self.log.emit("Brak wpisów pending")
                    break

                # Nowy chat co 10 wpisów (omijamy pierwszy wpis gdy entry_count == 0)
                if entry_count > 0 and entry_count % 10 == 0:
                    self.log.emit(f"Przetworzono {entry_count} wpisów. Otwieranie nowego chatu...")
                    prompter.new_chat()

                entry_id = pending["id"]
                link = pending["link"]

                self.log.emit(f"LLM: przetwarzanie wpisu {entry_id}")

                try:
                    full_prompt = f"{my_prompt} Link: {link}"
                    raw_response = prompter.send_prompt(full_prompt)
                    parsed_response = self._parse_response(raw_response)

                    success = self.entry_repo.update_llm(entry_id, parsed_response)

                    if not success:
                        self.error.emit(f"LLM: nie udało się zapisać wyniku dla {entry_id}")
                        break

                    updated_entry = self.entry_repo.get_by_id(entry_id)

                    if updated_entry is None:
                        self.error.emit(f"LLM: zapisano wynik, ale nie znaleziono wpisu {entry_id}")
                        break

                    entry_count += 1
                    self.result.emit(updated_entry)
                    self.log.emit(f"LLM: zakończono wpis {entry_id}")

                except Exception as exc:
                    self.error.emit(f"LLM worker error dla {entry_id}: {exc}")
                    prompter.new_chat()
                    time.sleep(2)
                    continue

                time.sleep(0.2)

        finally:
            self.log.emit("LLM queue finished")
            self.finished.emit()

    @staticmethod
    def _parse_response(response: str) -> LLMResponse:
        response = response.strip()

        if not response:
            raise ValueError("LLM zwrócił pustą odpowiedź")

        parsed: Any = json.loads(response)

        if not isinstance(parsed, dict):
            raise ValueError("Odpowiedź LLM nie jest obiektem JSON")

        required_fields = {"relevant", "company", "ticker", "forecast", "sector"}
        if set(parsed) != required_fields:
            raise ValueError("Odpowiedź LLM ma nieprawidłowe pola")

        allowed_forecasts = {
            "Silny spadek",
            "Spadek",
            "Neutralny",
            "Wzrost",
            "Silny wzrost",
        }
        allowed_sectors = {
            "zbrojeniowy",
            "dronowy",
            "medyczny",
            "hi-tech",
            "kosmiczny",
            "other",
        }

        if not isinstance(parsed["relevant"], bool):
            raise ValueError("Pole relevant musi być typu boolean")
        if parsed["sector"] not in allowed_sectors:
            raise ValueError("Nieprawidłowa wartość pola sector")

        if parsed["relevant"]:
            if not isinstance(parsed["company"], str) or not parsed["company"].strip():
                raise ValueError("Pole company musi zawierać nazwę spółki")
            if not isinstance(parsed["ticker"], str) or not parsed["ticker"].strip():
                raise ValueError("Pole ticker musi zawierać symbol spółki")
            if parsed["forecast"] not in allowed_forecasts:
                raise ValueError("Nieprawidłowa wartość pola forecast")
        elif parsed["company"] is not None or parsed["ticker"] is not None:
            raise ValueError("Dla relevant=false company i ticker muszą być null")
        elif parsed["forecast"] is not None or parsed["sector"] != "other":
            raise ValueError("Dla relevant=false forecast musi być null, a sector musi być other")

        return cast(LLMResponse, parsed)
