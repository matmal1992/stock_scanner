import traceback

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout

from stock_scanner.ui.gui_elements.Lines import HLine, VLine
from stock_scanner.ui.windows.base_window import BaseWindow
from stock_scanner.ui.workers.rss_feed_worker import RSSWorker


class NewsTrackerWindow(BaseWindow):
    """News tracker window."""

    def __init__(self) -> None:
        super().__init__("News Tracker")

        self.thread: QThread | None = None
        self.worker: RSSWorker | None = None

    def setup_ui(self) -> None:
        add_btn = QPushButton("Add")
        remove_btn = QPushButton("Remove")
        stop_btn = QPushButton("Stop tracking")
        stop_btn.setEnabled(False)
        add_btn.setEnabled(False)
        remove_btn.setEnabled(False)
        get_rss_feed_btn = QPushButton("Get RSS feed")
        get_rss_feed_btn.clicked.connect(self.start_rss)

        self.status = QTextEdit()
        self.status.setReadOnly(True)

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
        self.thread = QThread()
        self.worker = RSSWorker()

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)

        self.worker.log.connect(self.on_log)
        self.worker.error.connect(self.on_error)
        self.worker.data_ready.connect(self.on_data_ready)

        # najpierw quit thread
        self.worker.finished.connect(self.thread.quit)

        #  po zakończeniu thread cleanup
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # reset referencji
        self.thread.finished.connect(lambda: setattr(self, "thread", None))
        self.thread.finished.connect(lambda: setattr(self, "worker", None))

        self.thread.start()

    def on_log(self, text: str) -> None:
        self.status.append(f"[LOG] {text}")

    def on_error(self, e: str) -> None:
        print("ERROR:", e)
        print(traceback.format_exc())

    def on_data_ready(self, titles: list) -> None:
        self.status.append("\nNajnowsze wiadomości:\n")

        for title in titles:
            self.status.append(f"• {title}")

    def on_finished(self) -> None:
        self.status.append("\nZakończono.\n")

        self.status_label.setText("RSS pobrany")
        self.status_label.setStyleSheet("color: #00ff99;")

        self.thread = None
        self.worker = None

    # def showEvent(self, event: QShowEvent) -> None:
    #     super().showEvent(event)

    #     if not self.tracker_off and self.thread is None:
    #         self.start_strategy()

    # def start_strategy(self) -> None:
    #     self.status_label.setText("Tracking news...")
    #     self.status_label.setStyleSheet("color: #00ff99;")

    #     self.thread = QThread()
    #     # self.worker = NewsTrackerWorker()

    #     self.worker.moveToThread(self.thread)

    #     self.thread.started.connect(self.worker.run)
    #     self.worker.progressUpdated.connect(self.on_progress)

    #     self.worker.logUpdated.connect(self.on_logs_updated)
    #     self.worker.errorOccurred.connect(self.on_error)
    #     self.worker.finished.connect(self.on_finished)

    #     self.worker.finished.connect(self.thread.quit)

    #     self.thread.start()

    # def on_logs_updated(self, text: str) -> None:
    #     self.status.append(text)

    # def on_error(self, error: str) -> None:
    #     self.status.append(error)

    # def on_finished(self) -> None:
    #     self.tracker_off = True

    #     self.status_label.setText("Strategy finished")
    #     self.status_label.setStyleSheet("color: #00ff99;")

    #     self.console_btn.setEnabled(True)
    #     self.logs_btn.setEnabled(True)
    #     self.report_btn.setEnabled(True)
