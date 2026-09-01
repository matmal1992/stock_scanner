import logging
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

from src.stock_scanner.core.telegram import send_telegram_message
from src.stock_scanner.core.utils import get_actual_time
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry
from src.stock_scanner.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.stock_scanner.ui.workers.gpw_worker import GPWService
from src.stock_scanner.ui.workers.llm_worker import LLMService
from src.stock_scanner.ui.workers.new_connect_worker import NewConnectService

logger = logging.getLogger(__name__)


class NewsFeedList(QWidget):
    selection_changed = Signal(int)
    notify = Signal(str, str)

    def __init__(self, entry_repo: EntryRepository, tracked_repo: TrackedTickerRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo

        self.gpw = GPWService(entry_repo)
        self.gpw.result.connect(self.on_gpw_result)
        self.gpw.log.connect(self.on_gpw_log)
        self.gpw.error.connect(self.on_gpw_error)
        self.gpw.finished.connect(self.on_gpw_finished)

        self.new_connect = NewConnectService(entry_repo)
        self.new_connect.result.connect(self.on_new_connect_result)
        self.new_connect.log.connect(self.on_new_connect_log)
        self.new_connect.error.connect(self.on_new_connect_error)
        self.new_connect.finished.connect(self.on_new_connect_finished)

        self.llm = LLMService(entry_repo)
        self.llm.log.connect(self.on_llm_log)
        self.llm.error.connect(self.on_llm_error)
        self.llm.finished.connect(self.on_llm_finished)
        self.llm.result.connect(self.on_llm_result)

        self._ids: list[int | None] = []
        self.selected_entry_id: int | None = None

        self.feed_list = QTableWidget()
        self.feed_list.setSortingEnabled(False)
        self.feed_list.setSelectionBehavior(self.feed_list.SelectionBehavior.SelectRows)
        self.feed_list.verticalHeader().setVisible(False)
        self.feed_list.setColumnCount(5)
        self.feed_list.setHorizontalHeaderLabels(["Published", "Type", "Title", "LLM", "Sentiment"])
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
        self.feed_list.setColumnWidth(0, 120)
        self.feed_list.setColumnWidth(1, 80)
        self.feed_list.setColumnWidth(3, 90)
        self.feed_list.setColumnWidth(4, 90)

        start_scraping_btn = QPushButton("Start scraping")
        self.load_data_btn = QPushButton("Load data")
        self.run_llm_btn = QPushButton("Run LLM")
        self.clear_database_btn = QPushButton("Clear database")

        start_scraping_btn.clicked.connect(self.on_start_scraping_clicked)
        self.load_data_btn.clicked.connect(self._update_list)
        self.run_llm_btn.clicked.connect(self.on_run_llm_clicked)

        test_buttons_box = QHBoxLayout()
        test_buttons_box.addWidget(start_scraping_btn)
        test_buttons_box.addWidget(self.load_data_btn)
        test_buttons_box.addWidget(self.run_llm_btn)

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
            self.feed_list.setItem(row_idx, 3, QTableWidgetItem(data["llm"]))
            self.feed_list.setItem(row_idx, 4, QTableWidgetItem(data["sentiment"]))

            self._ids.append(entry_id)

    def format_rows(self, rows: Sequence[NewsEntry]) -> list[tuple[dict, int]]:
        result: list[tuple[dict, int]] = []

        for row in rows:
            formatted = {
                "published": str(row["published"]),
                "type": str(row["source_type"]),
                "title": row["title"][:100],
                "llm": str(row["llm"]),
                "sentiment": str(row["sentiment"]),
            }

            result.append((formatted, row["id"]))

        return result

    def _update_list(self) -> None:
        rows = self.entry_repo.get_all_entries()
        self.set_items(self.format_rows(rows))

    def on_llm_log(self, text: str) -> None:
        self.notify.emit(text, "neutral")

    def on_llm_error(self, text: str) -> None:
        logger.error(f"{get_actual_time()} - LLM ERROR: {text}")
        self.notify.emit(text, "error")

    def on_llm_finished(self) -> None:
        logger.info(f"{get_actual_time()} - Kolejka LLM zakończona")
        self.notify.emit("Kolejka LLM zakończona", "ok")

    def on_run_llm_clicked(self) -> None:
        if self.llm.is_running():
            self.notify.emit("LLM już działa", "error")
            return

        self.notify.emit("Uruchamiam kolejkę LLM...", "neutral")
        started = self.llm.start()

        if not started:
            logger.error(f"{get_actual_time()} - LLM ERROR: Nie udało się uruchomić LLM")
            self.notify.emit("Nie udało się uruchomić LLM", "error")

    def on_llm_result(self, entry: NewsEntry) -> None:
        self.notify.emit(f"LLM zakończony dla wpisu {entry['id']}", "ok")
        self._update_list()

        forecast_value = entry["llm"]
        self.notify.emit(f"LLM forecast: '{forecast_value}'", "neutral")

        if forecast_value not in ("Wzrost", "Silny wzrost"):
            msg = f"Forecast '{forecast_value}' — alert niespełniony"
            self.notify.emit(msg, "neutral")
            return

        self.notify.emit(f"Wysyłam alert Telegrama dla '{forecast_value}'", "ok")
        send_telegram_message(entry)

    def on_start_scraping_clicked(self) -> None:
        if self.gpw.is_running() or self.new_connect.is_running():
            self.notify.emit("Scraping już trwa", "error")
            return

        self.notify.emit("Start scraping", "neutral")
        self.gpw.start()
        self.new_connect.start()

    def on_gpw_result(self, has_new_entries: bool) -> None:
        self._update_list()

        if has_new_entries:
            if not self.llm.is_running():
                self.llm.start()
            self.notify.emit("Pobrano nowe komunikaty gpw", "ok")
        else:
            self.notify.emit("Brak nowych komunikatów gpw", "neutral")

    def on_gpw_log(self, text: str) -> None:
        self.notify.emit(text, "neutral")

    def on_gpw_error(self, text: str) -> None:
        logger.error(f"{get_actual_time()} - GPW ERROR: {text}")
        self.notify.emit(f"{get_actual_time()} Błąd GPW: {text}", "error")

    def on_gpw_finished(self) -> None:
        self.notify.emit("Pojedyncze pobieranie GPW zakończone", "ok")

    def on_new_connect_result(self, has_new_entries: bool) -> None:
        self._update_list()

        if has_new_entries:
            if not self.llm.is_running():
                self.llm.start()
            self.notify.emit("Pobrano nowe komunikaty New Connect", "ok")
        else:
            self.notify.emit("Brak nowych komunikatów New Connect", "neutral")

    def on_new_connect_log(self, text: str) -> None:
        self.notify.emit(text, "neutral")

    def on_new_connect_error(self, text: str) -> None:
        logger.error(f"{get_actual_time()} - New Connect ERROR: {text}")
        self.notify.emit(f"{get_actual_time()} Błąd New Connect: {text}", "error")

    def on_new_connect_finished(self) -> None:
        self.notify.emit("Pojedyncze pobieranie New Connect zakończone", "ok")
