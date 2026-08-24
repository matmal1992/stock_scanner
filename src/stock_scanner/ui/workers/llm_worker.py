import time

import pyautogui
import pyperclip
from PySide6.QtCore import QObject, QThread, Signal

from src.stock_scanner.core.gui_automations import (
    find_last_copy_icon,
    paste_into_input,
    scroll_to_bottom,
)
from src.stock_scanner.strategies.news_tracker.entry_repo import (
    EntryRepository,
    NewsEntry,
)

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

indeksów,
surowców,
walut,
obligacji,
stóp procentowych,
gospodarki,
całych sektorów,
krajów,
rynków jako całości,
trendów giełdowych,
innych instrumentów niż konkretnej spółki.

Jeżeli artykuł nie dotyczy bezpośrednio konkretnej, notowanej na giełdzie spółki, odpowiedz wyłącznie:

NIE DOTYCZY

KROK 2 — PROGNOZA

Jeżeli artykuł dotyczy bezpośrednio konkretnej spółki giełdowej,
oceń prawdopodobny wpływ informacji na kurs jej akcji.

Uwzględnij przede wszystkim informacje zawarte w artykule,
a dodatkowo — jeżeli są dostępne — aktualne wyniki finansowe, dane techniczne, rekomendacje analityków, 
prognozy, strategię spółki i inne istotne aktualne informacje. Bazuj wyłącznie na najnowszych (w odniesieniu 
do daty i godziny niniejszego prompta) danych.

Prognoza może przyjąć wyłącznie jedną z wartości:

Silny spadek
Spadek
Neutralny
Wzrost
Silny wzrost

KROK 3 — WALIDACJA

Przed wysłaniem odpowiedzi sprawdź:

czy rzeczywiście otworzyłeś i przeanalizowałeś wskazany link,
czy spółka jest konkretną spółką giełdową,
czy artykuł dotyczy jej bezpośrednio,
czy prognoza jest dokładnie jedną z pięciu dozwolonych wartości,
czy nie pozostawiłeś żadnych placeholderów typu [pełna nazwa spółki],
czy odpowiedź nie zawiera żadnego komentarza, uzasadnienia, źródła ani linku.

OSTATECZNA ODPOWIEDŹ MUSI BYĆ DOKŁADNIE JEDNYM Z DWÓCH FORMATÓW:

ODRZUCONO

ALBO

Nazwa instrumentu: [rzeczywista pełna nazwa spółki], Symbol instrumentu: [rzeczywisty symbol giełdowy], 
Prognoza: [jedna z pięciu dozwolonych wartości].

Nie zwracaj instrukcji, szablonu ani placeholderów. Zwróć wyłącznie wynik analizy.
"""

#     "Analiza ma charakter wyłącznie edukacyjny/informacyjny "
#     "i nie stanowi porady inwestycyjnej."


class ManualPromptWorker(QObject):
    def run(self, link: str) -> str:
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
            # self.response_received.emit(self.entry_id, response)
            # print("RESPONSE:\n", response)

            return response

        except Exception as exc:
            message = f"LLM worker error: {exc}"
            print(message)
            return ""


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

        try:
            while self.running:
                pending = self.entry_repo.get_last_pending()

                if pending is None:
                    self.log.emit("Brak wpisów pending")
                    break

                entry_id = pending["id"]
                link = pending["link"]

                self.log.emit(f"LLM: przetwarzanie wpisu {entry_id}")

                try:
                    response = self.prompt_worker.run(link)

                    success = self.entry_repo.update_llm(
                        entry_id,
                        response,
                    )

                    if not success:
                        self.log.emit(f"LLM: nie udało się zapisać wyniku dla {entry_id}")
                        break

                    updated_entry = self.entry_repo.get_by_id(entry_id)

                    if updated_entry is None:
                        self.error.emit(f"LLM: zapisano wynik, ale nie znaleziono wpisu {entry_id}")
                        break

                    self.result.emit(updated_entry)
                    self.log.emit(f"LLM: zakończono wpis {entry_id}")

                except Exception as exc:
                    self.error.emit(f"LLM worker error dla {entry_id}: {exc}")
                    break

                time.sleep(0.2)

        finally:
            self.log.emit("LLM queue finished")
            self.finished.emit()
