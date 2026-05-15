from PySide6.QtCore import QThread
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout

from stock_scanner.ui.windows.base_window import BaseWindow
from stock_scanner.ui.workers.three_tier_worker import ThreeTierWorker


class ThreeTierWindow(BaseWindow):
    """Three-tier strategy window."""

    def __init__(self) -> None:
        super().__init__("Three-Tier Strategy")

        self.thread: QThread | None = None
        self.worker: ThreeTierWorker | None = None

        self.strategy_finished = False

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        # ===== TOP BAR =====
        top_bar = QHBoxLayout()

        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.backRequested.emit)

        self.console_btn = QPushButton("Show console output")
        self.console_btn.setEnabled(False)

        self.logs_btn = QPushButton("Show logs")
        self.logs_btn.setEnabled(False)

        self.report_btn = QPushButton("Show report")
        self.report_btn.setEnabled(False)

        top_bar.addWidget(self.back_btn)
        top_bar.addWidget(self.console_btn)
        top_bar.addWidget(self.logs_btn)
        top_bar.addWidget(self.report_btn)
        top_bar.addStretch()

        # ===== TITLE =====
        title_label = QLabel("Three-Tier Strategy")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        # ===== STATUS =====
        self.status_label = QLabel("Strategy not started")
        self.status_label.setStyleSheet("color: orange; font-size: 14px;")

        # ===== CONSOLE =====
        self.console = QTextEdit()
        self.console.setReadOnly(True)

        layout.addLayout(top_bar)
        layout.addWidget(title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.console)

        self.setLayout(layout)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)

        if not self.strategy_finished and self.thread is None:
            self.start_strategy()

    def start_strategy(self) -> None:
        self.status_label.setText("Running strategy...")
        self.status_label.setStyleSheet("color: #00ff99;")

        self.thread = QThread()
        self.worker = ThreeTierWorker()

        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)

        self.worker.logUpdated.connect(self.on_logs_updated)
        self.worker.errorOccurred.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)

        self.worker.finished.connect(self.thread.quit)

        self.thread.start()

    def on_logs_updated(self, text: str) -> None:
        self.console.append(text)

    def on_error(self, error: str) -> None:
        self.console.append(error)

    def on_finished(self) -> None:
        self.strategy_finished = True

        self.status_label.setText("Strategy finished")
        self.status_label.setStyleSheet("color: #00ff99;")

        self.console_btn.setEnabled(True)
        self.logs_btn.setEnabled(True)
        self.report_btn.setEnabled(True)
