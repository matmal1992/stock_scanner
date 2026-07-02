import logging

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QVBoxLayout

from stock_scanner.ui.gui_elements.feed_list import NewsFeedList
from stock_scanner.ui.gui_elements.Labels import StatusLabel
from stock_scanner.ui.gui_elements.tracked_tickers_list import TrackedTickersList
from stock_scanner.ui.windows.base_window import BaseWindow
from stock_scanner.ui.workers.llm_worker import LLMService

logger = logging.getLogger(__name__)


class NewsTrackerWindow(BaseWindow):
    def __init__(self) -> None:
        self.tracked_tickers = TrackedTickersList(self)
        self.news_feed = NewsFeedList(self)

        super().__init__("News Tracker")
        self.llm = LLMService()
        # self.llm.result.connect(self.on_llm_result)
        self.website_thread: QThread | None = None
        self.notifications = StatusLabel(text="No notifications")

    # self.llm_thread: QThread | None = None
    #     self.timer = QTimer()
    #     self.timer.setInterval(10000)
    #     self.timer.timeout.connect(self.on_timer)

    # def on_timer(self) -> None:
    #     if self.rss_worker is None:
    #         self.getting_news()

    def setup_ui(self) -> None:
        self.status_label = StatusLabel(text="Status: standby")

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tracked_tickers)
        main_layout.addStretch(30)
        main_layout.addWidget(self.news_feed, stretch=1)
        main_layout.addWidget(self.notifications)

        self.setLayout(main_layout)

    # def _cleanup_llm_thread(self) -> None:
    # if self.llm_worker is not None:
    #     self.llm_worker.deleteLater()
    #     self.llm_worker = None
    # if self.llm_thread is not None:
    #     self.llm_thread.deleteLater()
    #     self.llm_thread = None
