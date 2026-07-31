from datetime import datetime
from typing import List, Sequence

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry, NewsFormatter
from src.strategies.news_tracker.news_fetcher import NewsFetcher
from src.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.ui.workers.llm_worker import ManualPromptWorker


class NewsFeedList(QWidget):
    selection_changed = Signal(int)
    notify = Signal(str, str)

    def __init__(self, entry_repo: EntryRepository, tracked_repo: TrackedTickerRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self._ids: List[int | None] = []

        self.feed_list = QListWidget()
        self.feed_list.itemSelectionChanged.connect(self.on_selection_changed)

        get_news_btn = QPushButton("Get feed")
        self.displ_link_btn = QPushButton("Display link")
        self.run_llm_btn = QPushButton("Run LLM")
        self.clear_database_btn = QPushButton("Clear database")
        get_news_btn.clicked.connect(self.on_get_espi_clicked)
        self.displ_link_btn.clicked.connect(self.on_display_link_clicked)
        self.run_llm_btn.clicked.connect(self.on_run_llm_clicked)
        self.clear_database_btn.clicked.connect(self.on_clear_database_clicked)
        self.run_llm_btn.setEnabled(False)
        self.displ_link_btn.setEnabled(False)

        self.fetcher = NewsFetcher(entry_repo, tracked_repo)
        self.fetcher.data_ready.connect(self.on_data_ready)
        self.fetcher.log.connect(self.on_log)
        self.fetcher.error.connect(self.on_error)

        test_buttons_box = QHBoxLayout()
        test_buttons_box.addWidget(get_news_btn)
        test_buttons_box.addWidget(self.displ_link_btn)
        test_buttons_box.addWidget(self.run_llm_btn)
        test_buttons_box.addWidget(self.clear_database_btn)

        layout = QVBoxLayout()
        layout.addLayout(test_buttons_box)
        layout.addWidget(self.feed_list)

        self.setLayout(layout)

    def set_items(self, items: Sequence[tuple[str, int | None]]) -> None:
        self.feed_list.clear()
        self._ids = []

        for text, entry_id in items:
            self.feed_list.addItem(text)
            self._ids.append(entry_id)

    def get_selected_id(self) -> int | None:
        index = self.feed_list.currentRow()
        if 0 <= index < len(self._ids):
            return self._ids[index]
        return None

    def on_selection_changed(self) -> None:
        self.selected_entry_id = self.get_selected_id()
        self.displ_link_btn.setEnabled(self.selected_entry_id is not None)
        self.run_llm_btn.setEnabled(self.selected_entry_id is not None)

    def on_display_link_clicked(self) -> None:
        if not self.selected_entry_id:
            self.notify.emit("Brak zaznaczonego wpisu", "error")
            return

        link = self.entry_repo.get_link_by_id(self.selected_entry_id)

        if not link:
            self.notify.emit("Nie znaleziono linku w bazie", "error")
            return

        self.notify.emit(f"Link: {link}", "neutral")
        QApplication.clipboard().setText(link)

    def on_run_llm_clicked(self) -> None:
        if not self.selected_entry_id:
            self.notify.emit("Run LLM: Brak zaznaczonego wpisu", "error")
            return

        link = self.entry_repo.get_link_by_id(self.selected_entry_id)
        if not link:
            self.notify.emit("Run LLM: Nie znaleziono linku w bazie", "error")
            return

        self.notify.emit("Running LLM...", "neutral")

        self.llm_worker = ManualPromptWorker(link, self.selected_entry_id)
        self.llm_worker.response_received.connect(self.on_llm_result)
        self.llm_worker.start()

    def on_clear_database_clicked(self) -> None:
        self.entry_repo.clear_all()
        self.set_items([("Brak danych", None)])
        self.displ_link_btn.setEnabled(False)
        self.run_llm_btn.setEnabled(False)
        self.notify.emit("Wyczyszczono bazę danych", "ok")

    def on_llm_result(self, entry_id: int, response: str) -> None:
        success = self.entry_repo.update_sentiment(entry_id, response)
        if success:
            self.notify.emit("LLM zakończony i zapisano wynik", "ok")
        else:
            self.notify.emit("LLM zakończony, ale nie zapisano wyniku", "error")

    def on_log(self, text: str) -> None:
        self.notify.emit(f"{text}", "neutral")
        # now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # self.set_status_item(0, f"{now} Status: {text}")

    def on_error(self, e: str) -> None:
        now = datetime.now()
        error_time = now.strftime("%Y-%m-%d %H:%M:%S")
        # self._set_status_item(0, f"{error_time} Błąd: {e}")
        self.notify.emit(f"{error_time} Błąd: {e}", "error")

    def on_data_ready(self, items: list[NewsEntry], has_new_entries: bool) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in items:
            self.entry_repo.save(item)

        rows_rss = self.entry_repo.get_latest_with_id("rss")
        formatted_rss = [(text, entry_id) for text, entry_id in NewsFormatter.format(rows_rss)]
        if has_new_entries:
            status_text = f"Nowe wpisy: {now}"
        else:
            status_text = f"{now}: Brak nowych wpisów"

        status_row: tuple[str, int | None] = (status_text, None)
        self.set_items([status_row, *formatted_rss])

    def on_get_espi_clicked(self) -> None:
        self.notify.emit("Pobieranie ESPI...", "neutral")
        self.fetcher.fetch()

        # self.espi_service = ESPIService(self.entry_repo)

        # self.espi_service.result.connect(self.on_data_ready)
        # self.espi_service.error.connect(self.on_error)
        # self.espi_service.log.connect(self.on_log)

        # self.espi_service.run()
