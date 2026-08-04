from datetime import datetime
from typing import Sequence

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
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
        self._ids: list[int | None] = []

        self.feed_list = QTableWidget()
        self.feed_list.setSortingEnabled(False)
        self.feed_list.setSelectionBehavior(self.feed_list.SelectionBehavior.SelectRows)
        self.feed_list.verticalHeader().setVisible(False)
        self.feed_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.feed_list.setColumnCount(5)
        self.feed_list.setHorizontalHeaderLabels(["Published", "Type", "Title", "LLM Status", "Sentiment"])
        self.feed_list.setStyleSheet("""
            QHeaderView {
                border: none;
            }
            QHeaderView::section {
                border: 1px solid #8f8f8f;
                background-color: #1e1e1e;
            }
            QTableWidget {
                gridline-color: #8f8f8f;
            }
            """)
        header = self.feed_list.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.feed_list.setColumnWidth(0, 140)
        self.feed_list.setColumnWidth(1, 80)
        self.feed_list.setColumnWidth(3, 100)
        self.feed_list.setColumnWidth(4, 100)

        get_news_btn = QPushButton("Get feed")
        self.load_data_btn = QPushButton("Load data")
        self.run_llm_btn = QPushButton("Run LLM")
        self.clear_database_btn = QPushButton("Clear database")
        get_news_btn.clicked.connect(self.on_get_espi_clicked)
        self.load_data_btn.clicked.connect(self.on_load_data_clicked)
        self.run_llm_btn.clicked.connect(self.on_run_llm_clicked)
        self.clear_database_btn.clicked.connect(self.on_clear_database_clicked)
        self.run_llm_btn.setEnabled(False)

        self.fetcher = NewsFetcher(entry_repo, tracked_repo)
        self.fetcher.data_ready.connect(self.on_data_ready)
        self.fetcher.log.connect(self.on_log)
        self.fetcher.error.connect(self.on_error)

        test_buttons_box = QHBoxLayout()
        test_buttons_box.addWidget(get_news_btn)
        test_buttons_box.addWidget(self.load_data_btn)
        test_buttons_box.addWidget(self.run_llm_btn)
        test_buttons_box.addWidget(self.clear_database_btn)

        layout = QVBoxLayout()
        layout.addLayout(test_buttons_box)
        layout.addWidget(self.feed_list)

        self.setLayout(layout)

    def set_items(self, items: Sequence[tuple[dict, int | None]]) -> None:
        self.feed_list.setRowCount(0)
        self._ids = []

        for row_idx, (data, entry_id) in enumerate(items):
            self.feed_list.insertRow(row_idx)

            self.feed_list.setItem(row_idx, 0, QTableWidgetItem(data["published"]))
            self.feed_list.setItem(row_idx, 1, QTableWidgetItem(data["type"]))
            self.feed_list.setItem(row_idx, 2, QTableWidgetItem(data["title"][:100]))
            self.feed_list.setItem(row_idx, 3, QTableWidgetItem(data["llm_status"]))
            self.feed_list.setItem(row_idx, 4, QTableWidgetItem(data["sentiment"]))

            self._ids.append(entry_id)

    def get_selected_id(self) -> int | None:
        row = self.feed_list.currentRow()
        if 0 <= row < len(self._ids):
            return self._ids[row]
        return None

    def on_selection_changed(self) -> None:
        self.selected_entry_id = self.get_selected_id()
        self.run_llm_btn.setEnabled(self.selected_entry_id is not None)

    def on_load_data_clicked(self) -> None:
        rows = self.entry_repo.get_all_entries()
        formatted_rows = NewsFormatter.format(rows)
        self.set_items(formatted_rows)

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
        self.set_items(
            [({"published": "", "type": "", "title": "Brak danych", "llm_status": "", "sentiment": ""}, None)]
        )
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

    def on_error(self, e: str) -> None:
        now = datetime.now()
        error_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self.notify.emit(f"{error_time} Błąd: {e}", "error")

    def on_data_ready(self, items: list[NewsEntry], has_new_entries: bool) -> None:
        for item in items:
            self.entry_repo.save(item)

        rows = self.entry_repo.get_all_entries()
        formatted_rows = [(text, entry_id) for text, entry_id in NewsFormatter.format(rows)]
        if has_new_entries:
            print("New entries")

        self.set_items([*formatted_rows])

    def on_get_espi_clicked(self) -> None:
        self.notify.emit("Pobieranie ESPI...", "neutral")
        self.fetcher.fetch()
