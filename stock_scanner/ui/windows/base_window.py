from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout, QWidget


class BaseWindow(QWidget):
    """Base class for strategy windows with common Back button and layout."""

    backRequested = Signal()

    def __init__(self, title: str) -> None:
        super().__init__()

        self.title = title
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        # back_btn = QPushButton("← Back")
        # back_btn.clicked.connect(self.backRequested.emit)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)

        # layout.addWidget(back_btn)
        layout.addWidget(self.content_widget)
        layout.addStretch()

        self.setLayout(layout)
