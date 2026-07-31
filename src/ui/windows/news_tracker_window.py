import logging

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.strategies.news_tracker.entry_repo import EntryRepository
from src.strategies.news_tracker.feed_list import NewsFeedList
from src.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.strategies.news_tracker.tracked_tickers_list import TrackedTickersList
from src.ui.gui_elements.Labels import StatusLabel
from src.ui.workers.llm_worker import LLMService

logger = logging.getLogger(__name__)


class NewsTrackerWindow(QWidget):
    def __init__(self, entry_repo: EntryRepository, tracked_repo: TrackedTickerRepository) -> None:
        super().__init__()
        self.llm = LLMService()
        self.entry_repo = entry_repo

        # self.llm.result.connect(self.on_llm_result)
        self.website_thread: QThread | None = None
        self.notifications = StatusLabel(text="No notifications")
        self.tracked_tickers = TrackedTickersList(tracked_repo)
        self.news_feed = NewsFeedList(entry_repo, tracked_repo)
        self.news_feed.notify.connect(self.on_notify)
        self.tracked_tickers.notify.connect(self.on_notify)

        self.setup_window_layout()

    # self.llm_thread: QThread | None = None
    #     self.timer = QTimer()
    #     self.timer.setInterval(10000)
    #     self.timer.timeout.connect(self.on_timer)

    # def on_timer(self) -> None:
    #     if self.rss_worker is None:
    #         self.getting_news()

    def setup_window_layout(self) -> None:
        self.status_label = StatusLabel(text="Status: standby")

        self.content_layout = QVBoxLayout(self)
        self.content_layout.addWidget(self.tracked_tickers)
        self.content_layout.addStretch(30)
        self.content_layout.addWidget(self.news_feed)
        self.content_layout.addStretch(10)
        self.content_layout.addWidget(self.notifications)

    def on_notify(self, text: str, level: str) -> None:
        if level == "ok":
            self.notifications.set_ok(text)
        elif level == "error":
            self.notifications.set_error(text)
        else:
            self.notifications.setText(text)

    # def _cleanup_llm_thread(self) -> None:
    # if self.llm_worker is not None:
    #     self.llm_worker.deleteLater()
    #     self.llm_worker = None
    # if self.llm_thread is not None:
    #     self.llm_thread.deleteLater()
    #     self.llm_thread = None
