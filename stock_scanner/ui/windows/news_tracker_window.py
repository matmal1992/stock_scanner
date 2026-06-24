import logging
import traceback
from datetime import datetime

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from stock_scanner.download.database import get_first_entry_link, has_entries
from stock_scanner.ui.gui_elements.Lines import HLine, VLine
from stock_scanner.ui.gui_elements.Lists import ListWidget
from stock_scanner.ui.windows.base_window import BaseWindow
from stock_scanner.ui.workers.google_news_worker import GoogleNewsWorker
from stock_scanner.ui.workers.llm_worker import ManualPromptWorker
from stock_scanner.ui.workers.rss_feed_worker import RSSWorker

logger = logging.getLogger(__name__)


class NewsTrackerWindow(BaseWindow):
    """News tracker window."""

    def __init__(self) -> None:
        super().__init__("News Tracker")

        self.rss_worker: RSSWorker | None = None
        self.google_worker: GoogleNewsWorker | None = None
        self.llm_worker: ManualPromptWorker | None = None

        # self.llm_thread: QThread | None = None
        self.website_thread: QThread | None = None

        self.latest_titles: list[str] = []
        self.status_links: list[str] = []

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

        self.status_label = QLabel("Tracker not working")
        self.status_label.setStyleSheet("color: orange; font-size: 14px;")

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
        if self.rss_worker is not None or self.google_worker is not None:
            return

        logger.info("Fetching RSS + Google News")

        self.rss_worker = RSSWorker()
        self.rss_worker.log.connect(self.on_log)
        self.rss_worker.error.connect(self.on_error)
        self.rss_worker.data_ready.connect(self.on_data_ready)
        self.rss_worker.finished.connect(lambda: setattr(self, "rss_worker", None))
        self.rss_worker.run()

        self.google_worker = GoogleNewsWorker()
        self.google_worker.log.connect(self.on_log)
        self.google_worker.error.connect(self.on_error)
        self.google_worker.data_ready.connect(self.on_data_ready)
        self.google_worker.finished.connect(lambda: setattr(self, "google_worker", None))
        self.google_worker.run()

        # if not self.timer.isActive():
        #     self.timer.start()

    def on_log(self, text: str) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._set_status_item(0, f"{now} Status: {text}")

    def on_error(self, e: str) -> None:
        now = datetime.now()
        error_time = now.strftime("%Y-%m-%d %H:%M:%S")
        self._set_status_item(0, f"{error_time} Błąd: {e}")
        self.status_label.setText("Błąd!")
        self.status_label.setStyleSheet("color: red; font-size: 14px;")
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

        lines = [status_text]
        self.status_links = []
        for title, link, published, source_type in items:
            prefix = f"[{source_type.upper()}]"
            self.status_links.append(link)

            if published:
                dt = datetime.fromtimestamp(published)
                time_str = dt.strftime("%d %b %H:%M")
                lines.append(f"{time_str} {prefix} {title}")
            else:
                lines.append(f"{prefix} {title}")

        self.status.set_items(lines, self.status_links)

    def _set_status_item(self, index: int, text: str) -> None:
        self.status.set_item(index, text)

    def on_test_llm_clicked(self) -> None:
        print("on_test_llm clicked")
        self.status_label.setText("Wysyłanie zapytania do LLM...")
        self.llm_worker = ManualPromptWorker(get_first_entry_link())
        self.llm_worker.response_received.connect(self.on_llm_result)

        # self.worker.response_received.connect(self.on_llm_result)
        self.llm_worker.start()

    def on_llm_result(self) -> None:
        self.status_label.setText("LLM zakończony")
        self.status_label.setStyleSheet("color: #00ff99; font-size: 14px;")

    # def _cleanup_llm_thread(self) -> None:
    # if self.llm_worker is not None:
    #     self.llm_worker.deleteLater()
    #     self.llm_worker = None
    # if self.llm_thread is not None:
    #     self.llm_thread.deleteLater()
    #     self.llm_thread = None
