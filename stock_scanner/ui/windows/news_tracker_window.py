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

from stock_scanner.core.email_alerts import send_gmail_alert
from stock_scanner.core.telegram import send_telegram_message
from stock_scanner.download.database import get_connection
from stock_scanner.ui.gui_elements.Lines import HLine, VLine
from stock_scanner.ui.windows.base_window import BaseWindow
from stock_scanner.ui.workers.llm_test_worker import GeminiWorker
from stock_scanner.ui.workers.rss_feed_worker import RSSWorker

logger = logging.getLogger(__name__)


class NewsTrackerWindow(BaseWindow):
    """News tracker window."""

    def __init__(self) -> None:
        super().__init__("News Tracker")

        self.worker: RSSWorker | None = None
        self.llm_thread: QThread | None = None
        self.llm_worker: GeminiWorker | None = None
        self.latest_titles: list[str] = []
        self.fetch_started_at: datetime | None = None

        self.timer = QTimer()
        self.timer.setInterval(10000)
        self.timer.timeout.connect(self.on_timer)

    def on_timer(self) -> None:
        if self.worker is None:
            self.start_rss()

    def setup_ui(self) -> None:
        add_btn = QPushButton("Add")
        remove_btn = QPushButton("Remove")
        self.test_llm_btn = QPushButton("Test LLM")
        self.test_llm_btn.setEnabled(False)
        add_btn.setEnabled(False)
        remove_btn.setEnabled(False)
        get_rss_feed_btn = QPushButton("Get RSS feed")
        get_rss_feed_btn.clicked.connect(self.start_rss)
        self.test_llm_btn.clicked.connect(self.on_test_llm_clicked)

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
        upper_layout.addWidget(QLabel("live chart"), stretch=2)

        main_layout = QVBoxLayout()
        main_layout.addLayout(upper_layout, stretch=1)
        main_layout.addWidget(HLine())
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(get_rss_feed_btn)
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

    def start_rss(self) -> None:
        if self.worker is not None:
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Get RSS feed button clicked")

        if send_telegram_message(f"<b>Get RSS feed</b> clicked at {now}"):
            logger.info("Telegram notification sent")
        else:
            logger.warning("Telegram notification not sent (missing config or error)")

        if send_gmail_alert("Stock Scanner Alert", f"<b>Get RSS feed</b> clicked at {now}"):
            logger.info("Gmail notification sent")
        else:
            logger.warning("Gmail notification not sent (missing config or error)")

        self.worker = RSSWorker()
        self.worker.log.connect(self.on_log)
        self.worker.error.connect(self.on_error)
        self.worker.data_ready.connect(self.on_data_ready)
        self.worker.finished.connect(lambda: setattr(self, "worker", None))
        self.worker.run()

        if not self.timer.isActive():
            self.timer.start()

    def on_log(self, text: str) -> None:
        now = datetime.now().strftime("[%H:%M:%S]")
        self._set_status_item(0, f"{now} Status: {text}")

    def on_error(self, e: str) -> None:
        now = datetime.now()
        error_time = now.strftime("[%H:%M:%S]")
        self._set_status_item(0, f"{error_time} Błąd: {e}")
        self.status_label.setText("Błąd!")
        self.status_label.setStyleSheet("color: red; font-size: 14px;")
        logger.info("ERROR:", e)
        logger.info(traceback.format_exc())

    def on_data_ready(self, items: list[tuple[int | None, str]], has_new_entries: bool) -> None:
        now = datetime.now()
        time_str = now.strftime("[%H:%M:%S]")

        if has_new_entries:
            self._set_status_item(0, f"Nowe wpisy: {time_str}")
            logger.info("Nowe wpisy")
            self.test_llm_btn.setEnabled(True)
        else:
            self._set_status_item(0, f"{time_str}: Brak nowych wpisów")
            self.test_llm_btn.setEnabled(self._has_rss_entries())

        for published, title in items:
            formatted = self.format_timestamp(published)
            pub_text = f"{formatted} • " if formatted else ""
            self._add_status_item(f"{pub_text}{title}")

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

    def _has_rss_entries(self) -> bool:
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
        # if self.llm_thread is not None:
        #     return

        # self.status_label.setText("Wysyłanie zapytania do LLM...")
        # self.status_label.setStyleSheet("color: orange; font-size: 14px;")
        # self.test_llm_btn.setEnabled(False)

        # self.llm_thread = QThread()
        # self.llm_worker = LLMTestWorker()
        # self.llm_worker.moveToThread(self.llm_thread)

        # self.llm_thread.started.connect(self.llm_worker.run)
        # self.llm_worker.result.connect(self.on_llm_result)
        # self.llm_worker.error.connect(self.on_error)
        # self.llm_worker.log.connect(self.on_log)
        # self.llm_worker.finished.connect(self.on_llm_finished)
        # self.llm_worker.finished.connect(self.llm_thread.quit)
        # self.llm_thread.finished.connect(self._cleanup_llm_thread)

        # self.llm_thread.start()

        self.status_label.setText("Wysyłanie zapytania do LLM...")
        # self.send_button.setEnabled(False) # Blokujemy przycisk na czas pracy

        # Uruchamiamy pracownika w osobnym wątku
        self.worker = GeminiWorker()
        # logger.info("Starting GeminiWorker thread")
        self.worker.response_received.connect(self.on_llm_result)
        self.worker.start()

    def on_llm_result(self, result: str) -> None:
        self._set_status_item(0, "Wynik LLM:")
        self._add_status_item(result)
        self.status_label.setText("LLM zakończony")
        self.status_label.setStyleSheet("color: #00ff99; font-size: 14px;")

    def on_llm_finished(self) -> None:
        self.test_llm_btn.setEnabled(self._has_rss_entries())

    def _cleanup_llm_thread(self) -> None:
        if self.llm_worker is not None:
            self.llm_worker.deleteLater()
            self.llm_worker = None
        if self.llm_thread is not None:
            self.llm_thread.deleteLater()
            self.llm_thread = None
