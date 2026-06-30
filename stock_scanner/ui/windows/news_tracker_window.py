import logging
import traceback
from datetime import datetime

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from stock_scanner.core.utils import FeedAdapter, NewsFormatter
from stock_scanner.download.database import (
    get_entry_link_by_id,
    get_latest_entries_with_id,
    insert_entry_raw,
)
from stock_scanner.download.news_fetcher import NewsFetcher
from stock_scanner.ui.gui_elements.Labels import StatusLabel
from stock_scanner.ui.gui_elements.Lines import HLine, VLine
from stock_scanner.ui.gui_elements.Lists import ListWidget
from stock_scanner.ui.windows.base_window import BaseWindow
from stock_scanner.ui.workers.llm_worker import LLMService, ManualPromptWorker

logger = logging.getLogger(__name__)


class NewsTrackerWindow(BaseWindow):
    def __init__(self) -> None:
        super().__init__("News Tracker")
        self.llm = LLMService()
        self.llm.result.connect(self.on_llm_result)
        self.website_thread: QThread | None = None
        self.selected_entry_id: str | None = None
        self.fetcher = NewsFetcher()
        self.fetcher.data_ready.connect(self.on_data_ready)
        self.fetcher.log.connect(self.on_log)
        self.fetcher.error.connect(self.on_error)
        self.tracked_data: list[dict] = []

    # self.llm_thread: QThread | None = None
    #     self.timer = QTimer()
    #     self.timer.setInterval(10000)
    #     self.timer.timeout.connect(self.on_timer)

    # def on_timer(self) -> None:
    #     if self.rss_worker is None:
    #         self.getting_news()

    def setup_ui(self) -> None:
        self.displ_link_btn = QPushButton("Display link")
        self.displ_link_btn.clicked.connect(self.on_display_link_clicked)
        self.add_to_tracked_btn = QPushButton("Add to tracked")
        self.add_to_tracked_btn.clicked.connect(self.on_add_tracked_clicked)
        self.test_llm_btn = QPushButton("Run LLM")
        self.test_llm_btn.setEnabled(False)
        self.displ_link_btn.setEnabled(False)
        get_news_btn = QPushButton("Get feed")
        get_news_btn.clicked.connect(self.getting_news)
        self.test_llm_btn.clicked.connect(self.on_run_llm_clicked)
        self.status = ListWidget()
        self.status.itemSelectionChanged.connect(self.on_selection_changed)
        self.status_label = StatusLabel()
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("Ticker (np. AAPL)")
        self.sources_input = QLineEdit()
        self.sources_input.setPlaceholderText("Źródła (np. bloomberg.com, reuters.com)")
        self.tracked_list = QListWidget()

        btn_list_layout = QHBoxLayout()
        btn_list_layout.addWidget(self.displ_link_btn)
        btn_list_layout.addWidget(self.add_to_tracked_btn)
        btn_list_layout.addWidget(self.test_llm_btn)

        list_layout = QVBoxLayout()
        list_layout.addLayout(btn_list_layout)
        list_layout.addWidget(self.ticker_input)
        list_layout.addWidget(self.sources_input)
        list_layout.addWidget(self.tracked_list)

        upper_layout = QHBoxLayout()
        upper_layout.addLayout(list_layout, stretch=1)
        upper_layout.addWidget(VLine())

        test_buttons_box = QHBoxLayout()
        test_buttons_box.addWidget(get_news_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(upper_layout, stretch=1)
        main_layout.addWidget(HLine())
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(test_buttons_box)
        main_layout.addWidget(self.status, stretch=1)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def on_add_tracked_clicked(self) -> None:
        ticker = self.ticker_input.text().strip().upper()
        sources = self.sources_input.text().strip()

        if not ticker:
            self.status_label.set_error("Podaj ticker")
            return

        if not sources:
            self.status_label.set_error("Podaj źródła")
            return

        # sprawdzenie duplikatu
        if any(t["ticker"] == ticker for t in self.tracked_data):
            self.status_label.set_error("Ticker już istnieje")
            return

        data = {
            "ticker": ticker,
            "sources": sources,
        }

        self.tracked_data.append(data)

        # dodanie do UI
        item_text = f"{ticker} - {sources}"
        item = QListWidgetItem(item_text)

        # 🔥 KLUCZ: przechowujemy dane w itemie
        item.setData(1, data)

        self.tracked_list.addItem(item)

        # cleanup
        self.ticker_input.clear()
        self.sources_input.clear()

        self.status_label.set_ok(f"Dodano {ticker}")

    def get_selected_tracked(self) -> dict | None:
        item = self.tracked_list.currentItem()
        if not item:
            return None

        return item.data(1)

    def remove_selected_tracked(self) -> None:
        row = self.tracked_list.currentRow()
        if row < 0:
            return

        item = self.tracked_list.takeItem(row)
        data = item.data(1)

        # usuń z modelu
        self.tracked_data = [t for t in self.tracked_data if t["ticker"] != data["ticker"]]

        self.status_label.set_ok(f"Usunięto {data['ticker']}")

    def on_selection_changed(self) -> None:
        self.selected_entry_id = self.status.get_selected_id()
        self.displ_link_btn.setEnabled(self.selected_entry_id is not None)
        self.test_llm_btn.setEnabled(self.selected_entry_id is not None)

    def on_display_link_clicked(self) -> None:
        if not self.selected_entry_id:
            print("Brak zaznaczonego wpisu")
            return

        link = get_entry_link_by_id(self.selected_entry_id)

        if not link:
            print("Nie znaleziono linku w bazie")
            return

        print(f"Selected link: {link}")

    def getting_news(self) -> None:
        logger.info("Fetching RSS + Google News")
        self.fetcher.fetch()

        # if not self.timer.isActive():
        #     self.timer.start()

    def on_log(self, text: str) -> None:
        print("on log" + text)
        # now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # self._set_status_item(0, f"{now} Status: {text}")

    def on_error(self, e: str) -> None:
        # now = datetime.now()
        # error_time = now.strftime("%Y-%m-%d %H:%M:%S")
        # self._set_status_item(0, f"{error_time} Błąd: {e}")
        self.status_label.set_error("Error")
        logger.info(f"ERROR: {e}")
        logger.info(traceback.format_exc())

    def on_data_ready(
        self, items: list[tuple[str, str, int | None, str]], has_new_entries: bool
    ) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. zapis do DB (czytelny i prosty)
        for item in items:
            insert_entry_raw(**FeedAdapter.to_db(item))

        # 2. DB → UI
        rows = get_latest_entries_with_id()
        formatted = NewsFormatter.format(rows)

        # 3. status
        if has_new_entries:
            status_text = f"Nowe wpisy: {now}"
        else:
            status_text = f"{now}: Brak nowych wpisów"

        # 4. UI update
        self.status.set_items([(status_text, "")] + formatted)

    # def _set_status_item(self, index: int, text: str) -> None:
    #     self.status.set_item(index, text)

    def on_run_llm_clicked(self) -> None:
        if not self.selected_entry_id:
            return

        link = get_entry_link_by_id(self.selected_entry_id)
        if not link:
            return

        self.status_label.setText("Wysyłanie zapytania do LLM...")

        self.llm_worker = ManualPromptWorker(link)
        self.llm_worker.response_received.connect(self.on_llm_result)
        self.llm_worker.start()

    def on_llm_result(self) -> None:
        self.status_label.set_ok("LLM zakończony")

    # def _cleanup_llm_thread(self) -> None:
    # if self.llm_worker is not None:
    #     self.llm_worker.deleteLater()
    #     self.llm_worker = None
    # if self.llm_thread is not None:
    #     self.llm_thread.deleteLater()
    #     self.llm_thread = None
