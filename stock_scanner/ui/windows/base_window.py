from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class BaseWindow(QWidget):
    """Base class for strategy windows with common Back button and layout."""

    backRequested = Signal()

    def __init__(self, title: str) -> None:
        super().__init__()

        self.title = title
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.backRequested.emit)

        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        content_label = QLabel(f"{self.title} window - Implement your strategy here")
        content_label.setStyleSheet("color: #888888; font-size: 14px;")

        layout.addWidget(back_btn)
        layout.addWidget(title_label)
        layout.addWidget(content_label)
        layout.addStretch()

        self.setLayout(layout)
