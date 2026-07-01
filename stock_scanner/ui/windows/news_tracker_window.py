import logging
import traceback
from datetime import datetime

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QVBoxLayout
from stock_scanner.core.utils import FeedAdapter, NewsFormatter
from stock_scanner.download.database import get_latest_entries_with_id, insert_entry_raw
from stock_scanner.download.news_fetcher import NewsFetcher
from stock_scanner.ui.gui_elements.Labels import StatusLabel
from stock_scanner.ui.gui_elements.feed_list import NewsFeedList
from stock_scanner.ui.gui_elements.tracked_tickers_list import TrackedTickersList
from stock_scanner.ui.windows.base_window import BaseWindow
from stock_scanner.ui.workers.llm_worker import LLMService

logger = logging.getLogger(__name__)


class NewsTrackerWindow(BaseWindow):
    def __init__(self) -> None:
        self.tracked_tickers = TrackedTickersList()
        self.news_feed = NewsFeedList()
        
        super().__init__("News Tracker")
        self.llm = LLMService()
        self.llm.result.connect(self.on_llm_result)
        self.website_thread: QThread | None = None
        self.selected_entry_id: str | None = None
        self.fetcher = NewsFetcher()
        self.fetcher.data_ready.connect(self.on_data_ready)
        self.fetcher.log.connect(self.on_log)
        self.fetcher.error.connect(self.on_error)

    # self.llm_thread: QThread | None = None
    #     self.timer = QTimer()
    #     self.timer.setInterval(10000)
    #     self.timer.timeout.connect(self.on_timer)

    # def on_timer(self) -> None:
    #     if self.rss_worker is None:
    #         self.getting_news()

    def setup_ui(self) -> None:
        self.status_label = StatusLabel()
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tracked_tickers)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.news_feed, stretch=1)
        main_layout.addStretch()

        self.setLayout(main_layout)

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

    

    # def _cleanup_llm_thread(self) -> None:
    # if self.llm_worker is not None:
    #     self.llm_worker.deleteLater()
    #     self.llm_worker = None
    # if self.llm_thread is not None:
    #     self.llm_thread.deleteLater()
    #     self.llm_thread = None
