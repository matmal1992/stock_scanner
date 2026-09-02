import subprocess
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from PySide6.QtCore import QObject, QThread, QTimer, Signal

# from src.stock_scanner.core.telegram import send_telegram_message
from src.stock_scanner.core.telegram import send_telegram_message
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry


class NewConnectWorker(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)

    URL = (
        "https://newconnect.pl/spolki-komunikaty-spolek?categoryRaports=ESPI&typeRaports=RB&searchText=&date="
    )

    def __init__(self, entry_repo: EntryRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo

    def run(self) -> None:
        self.log.emit("Start scrapowania New Connect")

        try:
            entries = self._scrape()

            self.log.emit(f"New Connect: znaleziono {len(entries)} komunikatów")

            has_new = self._save_entries(entries)

            self.result.emit(has_new)

        except Exception as exc:
            self.error.emit(f"New Connect error: {exc}")

    def _scrape(self) -> list[NewsEntry]:
        html = self._download()

        soup = BeautifulSoup(html, "html.parser")

        items = soup.select("#search-result > li")

        self.log.emit(f"New Connect: znaleziono {len(items)} elementów")

        results: list[NewsEntry] = []

        for i, item in enumerate(items):
            try:
                date_element = item.select_one("span.date")

                company_element = item.select_one("strong.name a")

                title_element = item.select_one("p")

                link_element = item.select_one("a[href^='komunikat?']")

                if not date_element:
                    self.log.emit(f"New Connect: brak daty dla elementu {i}")
                    continue

                if not company_element:
                    self.log.emit(f"New Connect: brak spółki dla elementu {i}")
                    continue

                if not title_element:
                    self.log.emit(f"New Connect: brak tytułu dla elementu {i}")
                    continue

                if not link_element:
                    self.log.emit(f"New Connect: brak linku dla elementu {i}")
                    continue

                date_str = date_element.get_text(" ", strip=True)[:19]

                company = company_element.get_text(" ", strip=True)

                title = title_element.get_text(" ", strip=True)

                link = link_element.get("href")

                if not isinstance(link, str):
                    self.log.emit(f"New Connect: nieprawidłowy link dla elementu {i}")
                    continue

                link = urljoin("https://www.newconnect.pl/", link)

                results.append(
                    {
                        "id": 0,
                        "title": title,
                        "link": link,
                        "published": date_str,
                        "source_type": "New Connect",
                        "ticker": company,
                        "llm": "pending",
                        "sentiment": "-",
                    }
                )

            except Exception as exc:
                self.log.emit(f"New Connect: błąd parsowania elementu {i}: {exc}")

        return results

    def _download(self) -> str:
        self.log.emit("New Connect: pobieranie przez curl...")

        result = subprocess.run(["curl.exe", "-s", "-L", self.URL], capture_output=True, timeout=30)

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace")

            raise RuntimeError(f"curl error {result.returncode}: {stderr}")

        html = result.stdout.decode("utf-8", errors="replace")

        if not html:
            raise RuntimeError("New Connect zwróciło pustą odpowiedź")

        return html

    def _save_entries(self, entries: list[NewsEntry]) -> bool:
        found_new = False

        for entry in entries:
            try:
                if self.entry_repo.save(entry):
                    send_telegram_message(entry)
                    found_new = True

            except Exception as exc:
                self.log.emit(f"New Connect: błąd zapisu: {exc}")

        return found_new


class NewConnectService(QObject):
    result = Signal(bool)
    error = Signal(str)
    log = Signal(str)
    finished = Signal()

    INTERVAL_MS = 5_000

    def __init__(
        self,
        entry_repo: EntryRepository,
    ) -> None:
        super().__init__()

        self.entry_repo = entry_repo

        self._thread: Optional[QThread] = None
        self.worker: Optional[NewConnectWorker] = None

        self._timer = QTimer(self)
        self._timer.setInterval(self.INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer)

    def start(self) -> bool:
        if self._timer.isActive():
            self.log.emit("Automatyczne pobieranie New Connect już działa")
            return False

        self.log.emit("Uruchamiam automatyczne pobieranie New Connect")

        self._run_once()
        self._timer.start()

        return True

    def stop(self) -> None:
        self._timer.stop()

        if self._thread is not None and self._thread.isRunning():
            self.log.emit("New Connect: oczekiwanie na zakończenie bieżącego scrapowania")
        else:
            self.log.emit("Automatyczne pobieranie New Connect zatrzymane")

    def is_running(self) -> bool:
        return self._timer.isActive() or (self._thread is not None and self._thread.isRunning())

    def _on_timer(self) -> None:
        self.log.emit("New Connect: czas na kolejne pobieranie")

        self._run_once()

    def _run_once(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            self.log.emit("New Connect: poprzednie scrapowanie jeszcze trwa")
            return

        self._thread = QThread()
        self.worker = NewConnectWorker(self.entry_repo)

        self.worker.moveToThread(self._thread)

        self.worker.result.connect(self._on_worker_result)

        self.worker.error.connect(self._on_worker_error)

        self.worker.log.connect(self.log)

        self.worker.result.connect(self._finish_worker)

        self.worker.error.connect(self._finish_worker)

        self._thread.started.connect(self.worker.run)

        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()

    def _on_worker_result(self, has_new: bool) -> None:
        self.result.emit(has_new)

    def _on_worker_error(self, message: str) -> None:
        self.error.emit(message)

    def _finish_worker(self) -> None:
        if self._thread is not None:
            self._thread.quit()

    def _on_thread_finished(self) -> None:
        if self.worker is not None:
            self.worker.deleteLater()

        self._thread = None
        self.worker = None

        self.finished.emit()
