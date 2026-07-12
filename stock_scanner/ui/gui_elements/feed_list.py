from datetime import datetime
from typing import List, Sequence, Tuple

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stock_scanner.core.utils import FeedAdapter, NewsFormatter
from stock_scanner.download.database import EntryRepository, TrackedTickerRepository
from stock_scanner.download.news_fetcher import NewsFetcher
from stock_scanner.ui.workers.llm_worker import ManualPromptWorker


class NewsFeedList(QWidget):
    selection_changed = Signal(str)
    notify = Signal(str, str)

    def __init__(self, entry_repo: EntryRepository, tracked_repo: TrackedTickerRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self._ids: List[str | None] = []

        self.feed_list = QListWidget()
        self.feed_list.itemSelectionChanged.connect(self.on_selection_changed)

        get_news_btn = QPushButton("Get feed")
        self.displ_link_btn = QPushButton("Display link")
        self.run_llm_btn = QPushButton("Run LLM")
        self.clear_database_btn = QPushButton("Clear database")
        get_news_btn.clicked.connect(self.on_get_news_clicked)
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

    def set_items(self, items: Sequence[Tuple[str, str | None]]) -> None:
        self.feed_list.clear()
        self._ids = []

        for text, entry_id in items:
            self.feed_list.addItem(text)
            self._ids.append(entry_id)

    def on_get_news_clicked(self) -> None:
        self.notify.emit("Pobieranie wiadomości...", "neutral")
        self.fetcher.fetch()

        # if not self.timer.isActive():
        #     self.timer.start()

    def get_selected_id(self) -> str | None:
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

    def on_run_llm_clicked(self) -> None:
        if not self.selected_entry_id:
            self.notify.emit("Run LLM: Brak zaznaczonego wpisu", "error")
            return

        link = self.entry_repo.get_link_by_id(self.selected_entry_id)
        if not link:
            self.notify.emit("Run LLM: Nie znaleziono linku w bazie", "error")
            return

        self.notify.emit("Running LLM...", "neutral")

        self.llm_worker = ManualPromptWorker(link)
        self.llm_worker.response_received.connect(self.on_llm_result)
        self.llm_worker.start()

    def on_clear_database_clicked(self) -> None:
        self.entry_repo.clear_all()
        self.set_items([("Brak danych", None)])
        self.displ_link_btn.setEnabled(False)
        self.run_llm_btn.setEnabled(False)
        self.notify.emit("Wyczyszczono bazę danych", "ok")

    def on_llm_result(self) -> None:
        self.notify.emit("LLM zakończony", "ok")

    def on_log(self, text: str) -> None:
        self.notify.emit(f"{text}", "neutral")
        # now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # self.set_status_item(0, f"{now} Status: {text}")

    def on_error(self, e: str) -> None:
        now = datetime.now()
        error_time = now.strftime("%Y-%m-%d %H:%M:%S")
        # self._set_status_item(0, f"{error_time} Błąd: {e}")
        self.notify.emit(f"{error_time} Błąd: {e}", "error")

    def on_data_ready(self, items: list[tuple[str, str, int | None, str]], has_new_entries: bool) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for item in items:
            data = FeedAdapter.to_db(item)
            self.entry_repo.save(**data)

        # rows_rss = self.entry_repo.get_latest_with_id("rss")
        rows_google = self.entry_repo.get_all_entries()
        # formatted_rss = NewsFormatter.format(rows_rss)
        formatted_google = NewsFormatter.format(rows_google)

        if has_new_entries:
            status_text = f"Nowe wpisy: {now}"
        else:
            status_text = f"{now}: Brak nowych wpisów"

        # self.set_items([(status_text, "neutral")] + formatted_rss + formatted_google)
        self.set_items([(status_text, "neutral")] + formatted_google)
