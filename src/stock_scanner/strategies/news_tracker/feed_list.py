import logging
from typing import Sequence

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry
from src.stock_scanner.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository

# from src.stock_scanner.telegram import TelegramBot

logger = logging.getLogger(__name__)

# dodać listę spółek z perspektywicznych sektorów: medyczny, obronny, dronowy hitech, kosmiczny...
# scrapers status: runtimowo coś jak notifications, tylko dla każdego workera
# runtimowe logi dla każdego workera, może w osobnej zakładce/oknie


class NewsFeedList(QWidget):
    selection_changed = Signal(int)
    notify = Signal(str, str)

    def __init__(self, entry_repo: EntryRepository, tracked_repo: TrackedTickerRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo
        self.entry_repo.changed.connect(self._update_list)

        self._ids: list[int | None] = []
        self.selected_entry_id: int | None = None

        self.feed_list = QTableWidget()
        self.feed_list.setSortingEnabled(False)
        self.feed_list.setSelectionBehavior(self.feed_list.SelectionBehavior.SelectRows)
        self.feed_list.verticalHeader().setVisible(False)
        self.feed_list.setColumnCount(5)
        self.feed_list.setHorizontalHeaderLabels(["Published", "Type", "Title", "LLM"])
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
        self.feed_list.setColumnWidth(0, 120)
        self.feed_list.setColumnWidth(1, 80)
        self.feed_list.setColumnWidth(2, 90)
        self.feed_list.setColumnWidth(3, 90)

        layout = QVBoxLayout()
        layout.addWidget(self.feed_list)
        self.setLayout(layout)
        self._update_list

    def set_items(self, items: Sequence[tuple[dict, int | None]]) -> None:
        self.feed_list.setRowCount(0)
        self._ids = []

        for row_idx, (data, entry_id) in enumerate(items):
            self.feed_list.insertRow(row_idx)

            self.feed_list.setItem(row_idx, 0, QTableWidgetItem(data["published"]))
            self.feed_list.setItem(row_idx, 1, QTableWidgetItem(data["type"]))
            self.feed_list.setItem(row_idx, 2, QTableWidgetItem(data["title"][:100]))
            self.feed_list.setItem(row_idx, 3, QTableWidgetItem(data["llm"]))

            self._ids.append(entry_id)

    def format_rows(self, rows: Sequence[NewsEntry]) -> list[tuple[dict, int]]:
        result: list[tuple[dict, int]] = []

        for row in rows:
            formatted = {
                "published": str(row["published"]),
                "type": str(row["source_type"]),
                "title": row["title"][:100],
                "llm": str(row["llm"]),
            }

            result.append((formatted, row["id"]))

        return result

    def _update_list(self) -> None:
        rows = self.entry_repo.get_all_entries()
        self.set_items(self.format_rows(rows))
