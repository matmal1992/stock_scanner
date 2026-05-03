from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from stock_scanner.ui.windows.base_window import BaseWindow


class NewsTrackerWindow(BaseWindow):
    """News tracker window."""

    def __init__(self) -> None:
        super().__init__("News Tracker")

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.backRequested.emit)

        title_label = QLabel("News Tracker")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        status_label = QLabel("News Tracker Window - Ready to implement")
        status_label.setStyleSheet("color: #00ccff; font-size: 14px;")

        layout.addWidget(back_btn)
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addStretch()

        self.setLayout(layout)
