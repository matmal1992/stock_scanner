import traceback
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)

from stock_scanner.ui.gui_elements.Lines import HLine, VLine
from stock_scanner.ui.windows.base_window import BaseWindow
from stock_scanner.ui.workers.rss_feed_worker import RSSWorker


class NewsTrackerWindow(BaseWindow):
    """News tracker window."""

    def __init__(self) -> None:
        super().__init__("News Tracker")

        self.worker: RSSWorker | None = None
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
        stop_btn = QPushButton("Stop tracking")
        stop_btn.setEnabled(False)
        add_btn.setEnabled(False)
        remove_btn.setEnabled(False)
        get_rss_feed_btn = QPushButton("Get RSS feed")
        get_rss_feed_btn.clicked.connect(self.start_rss)

        self.status = QListWidget()
        self.status.setAlternatingRowColors(False)
        self.status.setSelectionMode(QAbstractItemView.NoSelection)

        self.status_label = QLabel("Tracker not working")
        self.status_label.setStyleSheet("color: orange; font-size: 14px;")

        btn_list_layout = QHBoxLayout()
        btn_list_layout.addWidget(add_btn)
        btn_list_layout.addWidget(remove_btn)
        btn_list_layout.addWidget(stop_btn)

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

    def start_rss(self) -> None:
        if self.worker is not None:
            return

        self.worker = RSSWorker()

        self.worker.log.connect(self.on_log)
        self.worker.error.connect(self.on_error)
        self.worker.data_ready.connect(self.on_data_ready)
        # self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(lambda: setattr(self, "worker", None))

        # self.fetch_started_at = datetime.now()
        # start_time = self.fetch_started_at.strftime("[%H:%M:%S]")
        # self._set_status_item(0, f"Pobieranie... {start_time}")

        # self.status_label.setText("Pobieranie...")
        # self.status_label.setStyleSheet("color: #ffaa00; font-size: 14px;")

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
        print("ERROR:", e)
        print(traceback.format_exc())

    def on_data_ready(self, items: list[tuple[str, str]], has_new_entries: bool) -> None:
        now = datetime.now()
        time_str = now.strftime("[%H:%M:%S]")

        if has_new_entries:
            self._set_status_item(0, f"Nowe wpisy: {time_str}")
            for published, title in items:
                pub_text = f"{published} • " if published else ""
                self._add_status_item(f"{pub_text}{title}")
            # self.status_label.setText("RSS zaktualizowany")
            # self.status_label.setStyleSheet("color: #00ff99; font-size: 14px;")
        else:
            self._set_status_item(0, f"{time_str}: Brak nowych wpisów")
            # self.status_label.setText("Brak zmian")
            # self.status_label.setStyleSheet("color: #ffaa00; font-size: 14px;")

    # def on_finished(self) -> None:
    #     now = datetime.now()
    #     # finished_text = now.strftime("Ostatnia aktualizacja: [%H:%M:%S]")
    #     # self._set_status_item(0, finished_text)
    #     # self.status_label.setText(finished_text)
    #     # self.status_label.setStyleSheet("color: #00ff99; font-size: 14px;")

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
