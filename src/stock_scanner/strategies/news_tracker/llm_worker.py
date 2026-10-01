import logging

from PySide6.QtCore import QObject, QThread, Signal

from src.stock_scanner.core.gemini_prompter import GeminiPrompter
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry

logger = logging.getLogger(__name__)

my_prompt = """WYKONAJ PONIŻSZE POLECENIE DOSŁOWNIE.

Otwórz i przeanalizuj rzeczywistą treść artykułu znajdującego się pod podanym linkiem.

Nie zgaduj treści na podstawie tytułu, adresu URL ani innych metadanych. 
Jeżeli nie możesz uzyskać rzeczywistej treści artykułu, nie wymyślaj jej.

Artykuł zawsze będzie dotyczył konkretnej spółki giełdowej, notowanej na GPW lub na New Connect.

KROK 1 — ANALIZA INFORMACJI

Ustal na podstawie rzeczywistej treści artykułu:

Co dokładnie wydarzyło się według komunikatu?
Czy informacja jest potencjalnie pozytywna, negatywna czy neutralna dla spółki?
Czy informacja może mieć istotny wpływ na przyszłe wyniki finansowe, sytuację spółki lub jej wycenę?
Jaki jest potencjalny mechanizm wpływu tej informacji na kurs akcji?

Nie wymyślaj żadnych faktów ani danych.

KROK 2 — DANE DODATKOWE

Jeżeli są dostępne, uwzględnij najnowsze informacje dotyczące spółki, w szczególności:

- wyniki finansowe,
- prognozy,
- rekomendacje analityków,
- strategię spółki,
- istotne wydarzenia korporacyjne,
- inne informacje mogące mieć znaczenie dla oceny reakcji rynku.

Uwzględniaj wyłącznie informacje, które możesz rzeczywiście zweryfikować.
Bazuj wyłącznie na najnowszych dostępnych danych w odniesieniu do 
daty i godziny wykonania niniejszego polecenia.

KROK 3 — PROGNOZA

Oceń prawdopodobny wpływ analizowanej informacji na kurs akcji spółki.

Prognoza dotyczy reakcji kursu w ciągu 1-2 sesji giełdowych od momentu publikacji informacji.

Prognoza może przyjąć wyłącznie jedną z następujących wartości:

- "Silny spadek"
- "Spadek"
- "Neutralny"
- "Wzrost"
- "Silny wzrost"

KROK 4 — UZASADNIENIE

Napisz dokładnie dwa zdania uzasadnienia wybranej prognozy.

Uzasadnienie powinno wskazywać najważniejsze czynniki wynikające z analizowanej informacji oraz, 
jeżeli są istotne, z dodatkowych zweryfikowanych danych.

KROK 5 — FORMAT ODPOWIEDZI

Odpowiedź MUSI być poprawnym składniowo obiektem JSON, o strukturze:

{
  "forecast": "jedna z pięciu dozwolonych wartości",
  "justification": "Pierwsze zdanie uzasadnienia. Drugie zdanie uzasadnienia."
}

KROK 6 — WALIDACJA

Przed zwróceniem odpowiedzi sprawdź:

- Czy rzeczywiście uzyskałeś i przeanalizowałeś treść wskazanego linku.
- Czy nie wykorzystałeś informacji, których nie można zweryfikować.
- Czy prognoza jest dokładnie jedną z pięciu dozwolonych wartości.
- Czy uzasadnienie zawiera dokładnie dwa zdania.
- Czy odpowiedź jest poprawnym JSON-em.
- Czy JSON zawiera dokładnie pola "forecast" oraz "justification".
- Czy poza obiektem JSON nie znajduje się żaden dodatkowy tekst.
- Czy wartości tekstowe są prawidłowo escapowane zgodnie ze składnią JSON.
- Jeśli w tekście występują cudzysłowy, użyj apostrofów ' albo escapuj je jako \".

WAŻNE:

- Nie dodawaj komentarzy.
- Nie dodawaj źródeł.
- Nie dodawaj linków.
- Nie dodawaj Markdown.
- Nie używaj bloków ```json.
- Nie dodawaj tekstu przed ani po obiekcie JSON.
- Nie dodawaj dodatkowych pól.
- Nie zwracaj placeholderów.
- Nie wymyślaj brakujących informacji.

OSTATECZNA ODPOWIEDŹ MUSI ZAWIERAĆ WYŁĄCZNIE POPRAWNY OBIEKT JSON.

Analiza ma charakter wyłącznie edukacyjny i informacyjny.
"""


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
    result = Signal(NewsEntry)

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()

        self.entry_repo = entry_repo
        self.running = True
        # self.max_attempts_per_entry = 3 - odpuść po trzech nieudanych promptach

    def stop(self) -> None:
        self.running = False

    def run(self) -> None:
        self.log.emit("LLM queue started")
        prompter: GeminiPrompter | None = None

        try:
            self.log.emit("Uruchamianie przeglądarki...")
            prompter = GeminiPrompter()
            prompter.start()

            while self.running:
                pending = self.entry_repo.get_last_pending()

                if pending is None:
                    self.log.emit("Brak wpisów pending")
                    break

                entry_id = pending["id"]

                try:
                    self._process_entry(prompter=prompter, entry=pending)
                except Exception as exc:
                    logger.exception("LLM worker error dla %s", entry_id)
                    self.error.emit(f"LLM worker error dla {entry_id}: {exc}")
                    prompter.screenshot(name=f"llm_worker_exc_{entry_id}")
                    prompter.restart()
                    continue

                prompter.refresh()

        finally:
            if prompter is not None:
                try:
                    prompter.close()
                except Exception:
                    logger.exception("Błąd podczas zamykania sesji Gemini.")

            self.log.emit("LLM queue finished")
            self.finished.emit()

    def _process_entry(self, prompter: GeminiPrompter, entry: NewsEntry) -> None:
        entry_id = entry["id"]
        link = entry["link"]

        self.log.emit(f"LLM: przetwarzanie wpisu {entry_id}")

        full_prompt = f"{my_prompt} Link: {link}"

        response = prompter.send_prompt(full_prompt)

        success = self.entry_repo.update_llm(entry_id, response)
        if not success:
            raise RuntimeError(f"Nie udało się zapisać wyniku dla {entry_id}")

        updated_entry = self.entry_repo.get_by_id(entry_id)
        if updated_entry is None:
            raise RuntimeError(f"Zapisano wynik, ale nie znaleziono wpisu {entry_id}")

        self.result.emit(updated_entry)
        self.log.emit(f"LLM: zakończono wpis {entry_id}")
