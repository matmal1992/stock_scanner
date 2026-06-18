import logging
import traceback
from datetime import datetime

from PySide6.QtCore import QThread, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)

from stock_scanner.core.telegram import send_telegram_message
from stock_scanner.download.database import get_connection, get_first_entry_link
from stock_scanner.ui.gui_elements.Lines import HLine, VLine
from stock_scanner.ui.windows.base_window import BaseWindow
from stock_scanner.ui.workers.google_news_worker import GoogleNewsWorker
from stock_scanner.ui.workers.llm_test_worker import GeminiWorker
from stock_scanner.ui.workers.rss_feed_worker import RSSWorker
from stock_scanner.ui.workers.website_worker import WebsiteWorker

logger = logging.getLogger(__name__)


class NewsTrackerWindow(BaseWindow):
    """News tracker window."""

    def __init__(self) -> None:
        super().__init__("News Tracker")

        self.rss_worker: RSSWorker | None = None
        self.google_worker: GoogleNewsWorker | None = None
        self.llm_thread: QThread | None = None
        self.llm_worker: GeminiWorker | None = None
        self.latest_titles: list[str] = []
        self.fetch_started_at: datetime | None = None
        self.website_thread: QThread | None = None
        self.website_worker: WebsiteWorker | None = None

        self.timer = QTimer()
        self.timer.setInterval(10000)
        self.timer.timeout.connect(self.on_timer)

    def on_timer(self) -> None:
        if self.rss_worker is None:
            self.getting_news()

    def setup_ui(self) -> None:
        add_btn = QPushButton("Add")
        remove_btn = QPushButton("Remove")
        self.test_llm_btn = QPushButton("Test LLM")
        self.test_llm_btn.setEnabled(False)
        add_btn.setEnabled(False)
        remove_btn.setEnabled(False)
        get_news_btn = QPushButton("Get RSS feed")
        get_news_btn.clicked.connect(self.getting_news)
        self.test_llm_btn.clicked.connect(self.on_test_llm_clicked)
        extract_btn = QPushButton("Extract text")
        extract_btn.clicked.connect(self.on_extract_text_clicked)
        self.first_entry_link: str

        self.status = QListWidget()
        self.status.setAlternatingRowColors(False)
        self.status.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

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
        # upper_layout.addWidget(self.first_entry_link, stretch=2)

        main_layout = QVBoxLayout()
        main_layout.addLayout(upper_layout, stretch=1)
        main_layout.addWidget(HLine())
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(get_news_btn)
        main_layout.addWidget(extract_btn)
        main_layout.addWidget(self.status, stretch=1)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def format_timestamp(self, ts: int | None) -> str:
        if not ts:
            return ""
        try:
            ts = int(ts)
        except (ValueError, TypeError):
            return ""

        dt = datetime.fromtimestamp(ts)
        return dt.strftime("%d %b %H:%M:%S")

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

        if not self.timer.isActive():
            self.timer.start()

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
            self.test_llm_btn.setEnabled(self._has_entries())

        lines = [status_text]
        for title, link, published, source_type in items:
            prefix = f"[{source_type.upper()}]"

            if published:
                dt = datetime.fromtimestamp(published)
                time_str = dt.strftime("%d %b %H:%M")
                lines.append(f"{time_str} {prefix} {title}")
            else:
                lines.append(f"{prefix} {title}")

        self._update_status_list(lines)

    def _update_status_list(self, lines: list[str]) -> None:
        self.status.clear()
        self.status.addItems(lines)

    def _set_status_item(self, index: int, text: str) -> None:
        """Set status item at index, creating if needed."""
        while self.status.count() <= index:
            self.status.addItem("")
        self.status.item(index).setText(text)

    def _add_status_item(self, text: str) -> None:
        """Add a new item to status list without clearing."""
        self.status.addItem(text)

    def _has_entries(self) -> bool:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM entries LIMIT 1")
            exists = cur.fetchone() is not None
            return exists
        except Exception:
            return False
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def on_test_llm_clicked(self) -> None:
        if send_telegram_message("Hello from Stock Scanner!"):
            logger.info("Telegram notification sent")
        else:
            logger.warning("Telegram notification not sent (missing config or error)")

        self.status_label.setText("Wysyłanie zapytania do LLM...")
        self.worker = GeminiWorker()

        self.worker.response_received.connect(self.on_llm_result)
        self.worker.start()

    def on_llm_result(self, result: str) -> None:
        self._set_status_item(0, "Wynik LLM:")
        self._add_status_item(result)
        self.status_label.setText("LLM zakończony")
        self.status_label.setStyleSheet("color: #00ff99; font-size: 14px;")

    def on_llm_finished(self) -> None:
        self.test_llm_btn.setEnabled(self._has_entries())

    def _cleanup_llm_thread(self) -> None:
        if self.llm_worker is not None:
            self.llm_worker.deleteLater()
            self.llm_worker = None
        if self.llm_thread is not None:
            self.llm_thread.deleteLater()
            self.llm_thread = None

    def on_extract_text_clicked(self) -> None:
        if self.website_thread is not None:
            return

        self.first_entry_link = get_first_entry_link()
        logger.info("first_entry_link: %s", self.first_entry_link)

        self.status_label.setText("Scrapowanie strony...")
        self.status_label.setStyleSheet("color: orange; font-size: 14px;")

        self.website_thread = QThread()
        self.website_worker = WebsiteWorker(self.first_entry_link)
        self.website_worker.moveToThread(self.website_thread)

        self.website_thread.started.connect(self.website_worker.run)
        self.website_worker.result.connect(self.on_website_result)
        self.website_worker.error.connect(self.on_error)
        self.website_worker.log.connect(self.on_log)

        self.website_worker.finished.connect(self.website_thread.quit)
        self.website_worker.finished.connect(self._cleanup_website_thread)
        self.website_thread.finished.connect(self.website_thread.deleteLater)

        self.website_thread.start()

    def on_website_result(self, path: str) -> None:
        self._add_status_item(f"Zapisano plik: {path}")
        self.status_label.setText("Gotowe")
        self.status_label.setStyleSheet("color: #00ff99; font-size: 14px;")

    def _cleanup_website_thread(self) -> None:
        if self.website_worker is not None:
            self.website_worker.deleteLater()
            self.website_worker = None

        if self.website_thread is not None:
            self.website_thread = None
