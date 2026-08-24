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

from src.stock_scanner.core.telegram import send_telegram_message
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository, NewsEntry
from src.stock_scanner.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.stock_scanner.ui.workers.espi_worker import ESPIService
from src.stock_scanner.ui.workers.gpw_news_worker import NewsService
from src.stock_scanner.ui.workers.llm_worker import LLMService


class NewsFeedList(QWidget):
    selection_changed = Signal(int)
    notify = Signal(str, str)

    def __init__(self, entry_repo: EntryRepository, tracked_repo: TrackedTickerRepository) -> None:
        super().__init__()
        self.entry_repo = entry_repo

        self.espi = ESPIService(entry_repo)
        self.espi.result.connect(self.on_espi_result)
        self.espi.log.connect(self.on_espi_log)
        self.espi.error.connect(self.on_espi_error)
        self.espi.finished.connect(self.on_espi_finished)

        self.news = NewsService(entry_repo)
        self.news.result.connect(self.on_news_result)
        self.news.log.connect(self.on_news_log)
        self.news.error.connect(self.on_news_error)
        self.news.finished.connect(self.on_news_finished)

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
        # get_news_btn = QPushButton("Get News")
        self.load_data_btn = QPushButton("Load data")
        # self.stop_espi = QPushButton("Stop ESPI")
        self.run_llm_btn = QPushButton("Run LLM")
        self.clear_database_btn = QPushButton("Clear database")

        start_scraping_btn.clicked.connect(self.on_start_scraping_clicked)
        # get_news_btn.clicked.connect(self.on_get_news_clicked)
        self.load_data_btn.clicked.connect(self._update_list)
        self.run_llm_btn.clicked.connect(self.on_run_llm_clicked)
        self.clear_database_btn.clicked.connect(self.on_clear_database_clicked)
        # self.stop_espi.clicked.connect(self.on_stop_espi_clicked)

        test_buttons_box = QHBoxLayout()
        test_buttons_box.addWidget(start_scraping_btn)
        # test_buttons_box.addWidget(get_news_btn)
        test_buttons_box.addWidget(self.load_data_btn)
        test_buttons_box.addWidget(self.run_llm_btn)
        test_buttons_box.addWidget(self.clear_database_btn)
        # test_buttons_box.addWidget(self.stop_espi)

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
        self.notify.emit(text, "error")

    def on_llm_finished(self) -> None:
        self.notify.emit("Kolejka LLM zakończona", "ok")

    def on_run_llm_clicked(self) -> None:
        if self.llm.is_running():
            self.notify.emit("LLM już działa", "error")
            return

        self.notify.emit("Uruchamiam kolejkę LLM...", "neutral")
        started = self.llm.start()

        if not started:
            self.notify.emit("Nie udało się uruchomić LLM", "error")

    def on_llm_result(self, entry: NewsEntry) -> None:
        self.notify.emit(f"LLM zakończony dla wpisu {entry['id']}", "ok")
        self._update_list()

        if entry["llm"] not in ("Wzrost", "Silny wzrost"):
            return

        send_telegram_message(entry)

    def on_clear_database_clicked(self) -> None:
        if self.espi.is_running():
            self.notify.emit("Nie można wyczyścić bazy podczas pobierania ESPI", "error")
            return

        if self.llm.is_running():
            self.notify.emit("Nie można wyczyścić bazy podczas pracy LLM", "error")
            return

        self.entry_repo.clear_all()
        self.set_items(
            [({"published": "", "type": "", "title": "Brak danych", "llm": "", "sentiment": ""}, None)]
        )
        self.notify.emit("Wyczyszczono bazę danych", "ok")

    def on_espi_result(self, has_new_entries: bool) -> None:
        self._update_list()

        if has_new_entries:
            if not self.llm.is_running():
                self.llm.start()
            self.notify.emit("Pobrano nowe komunikaty ESPI", "ok")
        else:
            self.notify.emit("Brak nowych komunikatów ESPI", "neutral")

    # def on_get_espi_clicked(self) -> None:
    #     if self.espi.is_running():
    #         self.notify.emit("Pobieranie ESPI już trwa", "error")
    #         return

    #     self.notify.emit("Uruchamiam automatyczne pobieranie ESPI...", "neutral")
    #     started = self.espi.start()

    #     if not started:
    #         self.notify.emit("Nie udało się uruchomić ESPI", "error")

    def on_espi_log(self, text: str) -> None:
        self.notify.emit(text, "neutral")

    def on_espi_error(self, text: str) -> None:
        now = datetime.now()
        error_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self.notify.emit(f"{error_time} Błąd ESPI: {text}", "error")

    def on_espi_finished(self) -> None:
        self.notify.emit("Pojedyncze pobieranie ESPI zakończone", "ok")

    # def on_stop_espi_clicked(self) -> None:
    #     if not self.espi.is_running():
    #         self.notify.emit("Automatyczne ESPI nie jest uruchomione", "neutral")
    #         return

    #     self.espi.stop()
    #     self.notify.emit("Automatyczne pobieranie ESPI zatrzymane", "ok")

    def on_news_result(self, has_new_entries: bool) -> None:
        self._update_list()

        if has_new_entries:
            if not self.llm.is_running():
                self.llm.start()
            self.notify.emit("Pobrano nowe GPW Bankier News", "ok")
        else:
            self.notify.emit("Brak nowych GPW Bankier News", "neutral")

    def on_start_scraping_clicked(self) -> None:
        if self.news.is_running() or self.espi.is_running():
            self.notify.emit("Scraping już trwa", "error")
            return

        self.notify.emit("Start scraping", "neutral")
        started_news = self.news.start()
        started_espi = self.espi.start()

        if not started_news or started_espi:
            self.notify.emit("Nie udało się uruchomić scrapingu", "error")

    def on_news_log(self, text: str) -> None:
        self.notify.emit(text, "neutral")

    def on_news_error(self, text: str) -> None:
        now = datetime.now()
        error_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self.notify.emit(f"{error_time} Błąd ESPI: {text}", "error")

    def on_news_finished(self) -> None:
        self.notify.emit("Pojedyncze pobieranie GPW Bankier News zakończone", "ok")
