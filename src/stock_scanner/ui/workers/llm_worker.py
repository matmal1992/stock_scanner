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
    def run(self, link: str) -> str:
        try:
            prompt = f"{my_prompt} Link do analizy: {link}"
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
