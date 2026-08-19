from PySide6.QtCore import QThread
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.stock_scanner.ui.workers.three_tier_worker import ThreeTierWorker


class ThreeTierWindow(QWidget):
    """Three-tier strategy window."""

    def __init__(self) -> None:
        super().__init__()

        self.worker_thread: QThread | None = None
        self.worker: ThreeTierWorker | None = None

        self.strategy_finished = False

    def setup_ui(self) -> None:
        self.console_btn = QPushButton("Show console output")
        self.console_btn.setEnabled(False)

        self.logs_btn = QPushButton("Show logs")
        self.logs_btn.setEnabled(False)

        self.report_btn = QPushButton("Show report")
        self.report_btn.setEnabled(False)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.console_btn)
        top_bar.addWidget(self.logs_btn)
        top_bar.addWidget(self.report_btn)
        top_bar.addStretch()

        title_label = QLabel("Three-Tier Strategy")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.status_label = QLabel("Strategy not started")
        self.status_label.setStyleSheet("color: orange; font-size: 14px;")

        self.console = QTextEdit()
        self.console.setReadOnly(True)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addWidget(title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.console)

        self.setLayout(layout)

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)

        if not self.strategy_finished and self.worker_thread is None:
            self.start_strategy()

    def start_strategy(self) -> None:
        self.status_label.setText("Running strategy...")
        self.status_label.setStyleSheet("color: #00ff99;")

        self.worker_thread = QThread()
        self.worker = ThreeTierWorker()
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.progressUpdated.connect(self.on_progress)

        self.worker.logUpdated.connect(self.on_logs_updated)
        self.worker.errorOccurred.connect(self.on_error)
        self.worker.finished.connect(self.on_finished)

        self.worker.finished.connect(self.worker_thread.quit)

        self.worker_thread.start()

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

    def on_progress(self, value: int) -> None:
        self.progress_bar.setValue(value)
