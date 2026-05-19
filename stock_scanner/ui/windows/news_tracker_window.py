from PySide6.QtCore import QThread
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QLabel, QPushButton, QTextEdit, QVBoxLayout

from stock_scanner.ui.windows.base_window import BaseWindow


class NewsTrackerWindow(BaseWindow):
    """News tracker window."""

    def __init__(self) -> None:
        super().__init__("News Tracker")

        self.thread: QThread | None = None
        # self.worker: NewsTrackerWorker | None = None

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.backRequested.emit)

        stop_btn = QPushButton("Stop tracking")
        stop_btn.setEnabled(False)

        title_label = QLabel("News Tracker")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.status_label = QLabel("Tracker not working")
        self.status_label.setStyleSheet("color: orange; font-size: 14px;")

        self.status = QTextEdit()
        self.status.setReadOnly(True)

        status_label = QLabel("News Tracker Window - Ready to implement")
        status_label.setStyleSheet("color: #00ccff; font-size: 14px;")

        layout.addWidget(back_btn)
        layout.addWidget(stop_btn)
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addWidget(self.status)
        layout.addStretch()

        self.setLayout(layout)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)

        if not self.tracker_off and self.thread is None:
            self.start_strategy()

    def start_strategy(self) -> None:
        self.status_label.setText("Tracking news...")
        self.status_label.setStyleSheet("color: #00ff99;")

        self.thread = QThread()
        # self.worker = NewsTrackerWorker()

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progressUpdated.connect(self.on_progress)

        self.worker.logUpdated.connect(self.on_logs_updated)
        self.worker.errorOccurred.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)

        self.worker.finished.connect(self.thread.quit)

        self.thread.start()

    def on_logs_updated(self, text: str) -> None:
        self.status.append(text)

    def on_error(self, error: str) -> None:
        self.status.append(error)

    def on_finished(self) -> None:
        self.tracker_off = True

        self.status_label.setText("Strategy finished")
        self.status_label.setStyleSheet("color: #00ff99;")

        self.console_btn.setEnabled(True)
        self.logs_btn.setEnabled(True)
        self.report_btn.setEnabled(True)
