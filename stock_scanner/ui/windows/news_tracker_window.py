import logging
import traceback
from datetime import datetime

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from stock_scanner.download.database import get_first_entry_link, has_entries
from stock_scanner.ui.gui_elements.Lines import HLine, VLine
from stock_scanner.ui.gui_elements.Lists import ListWidget
from stock_scanner.ui.windows.base_window import BaseWindow
from stock_scanner.ui.workers.llm_worker import ManualPromptWorker, LLMService
from stock_scanner.download.news_fetcher import NewsFetcher
from stock_scanner.core.utils import NewsFormatter
from stock_scanner.ui.gui_elements.Labels import StatusLabel

logger = logging.getLogger(__name__)


class NewsTrackerWindow(BaseWindow):
    """News tracker window."""

    def __init__(self) -> None:
        super().__init__("News Tracker")
        # self.llm_worker: ManualPromptWorker | None = None
        self.llm = LLMService()
        self.llm.result.connect(self.on_llm_result)
        # self.llm_thread: QThread | None = None
        self.website_thread: QThread | None = None

        self.latest_titles: list[str] = []
        self.status_links: list[str] = []
        self.fetcher = NewsFetcher()
        self.fetcher.data_ready.connect(self.on_data_ready)
        self.fetcher.log.connect(self.on_log)
        self.fetcher.error.connect(self.on_error)

    #     self.timer = QTimer()
    #     self.timer.setInterval(10000)
    #     self.timer.timeout.connect(self.on_timer)

    # def on_timer(self) -> None:
    #     if self.rss_worker is None:
    #         self.getting_news()

    def setup_ui(self) -> None:
        add_btn = QPushButton("Add")
        remove_btn = QPushButton("Remove")
        self.test_llm_btn = QPushButton("Test LLM")
        self.test_llm_btn.setEnabled(False)
        add_btn.setEnabled(False)
        remove_btn.setEnabled(False)
        get_news_btn = QPushButton("Get feed")
        get_news_btn.clicked.connect(self.getting_news)
        self.test_llm_btn.clicked.connect(self.on_test_llm_clicked)
        self.first_entry_link: str
        self.status = ListWidget()
        self.status_label = StatusLabel()

        btn_list_layout = QHBoxLayout()
        btn_list_layout.addWidget(add_btn)
        btn_list_layout.addWidget(remove_btn)
        btn_list_layout.addWidget(self.test_llm_btn)

        list_layout = QVBoxLayout()
        list_layout.addLayout(btn_list_layout)
        list_layout.addWidget(QLabel("tracked tickers list"))

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

    def getting_news(self) -> None:
        logger.info("Fetching RSS + Google News")
        self.fetcher.fetch()

        # if not self.timer.isActive():
        #     self.timer.start()

    def on_log(self, text: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._set_status_item(0, f"{now} Status: {text}")

    def on_error(self, e: str) -> None:
        now = datetime.now()
        error_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self._set_status_item(0, f"{error_time} Błąd: {e}")
        self.status_label.set_error("Error")
        logger.info(f"ERROR: {e}")
        logger.info(traceback.format_exc())

    def on_data_ready(
        self, items: list[tuple[str, str, int | None, str]], has_new_entries: bool
    ) -> None:
        now = datetime.now()
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        if has_new_entries:
            status_text = f"Nowe wpisy: {time_str}"
            logger.info("Nowe wpisy")
            self.test_llm_btn.setEnabled(True)
        else:
            status_text = f"{time_str}: Brak nowych wpisów"
            self.test_llm_btn.setEnabled(has_entries())

        lines, links = NewsFormatter.format(items)
        self.status.set_items([status_text] + lines, links)

    def _set_status_item(self, index: int, text: str) -> None:
        self.status.set_item(index, text)

    def on_test_llm_clicked(self) -> None:
        link = self.status.get_selected_entry_link() or get_first_entry_link()
        self.status_label.set_warning("Wysyłanie zapytania do LLM...")
        self.llm.run(link)

    def on_llm_result(self) -> None:
        self.status_label.set_ok("LLM zakończony")

    # def _cleanup_llm_thread(self) -> None:
    # if self.llm_worker is not None:
    #     self.llm_worker.deleteLater()
    #     self.llm_worker = None
    # if self.llm_thread is not None:
    #     self.llm_thread.deleteLater()
    #     self.llm_thread = None
