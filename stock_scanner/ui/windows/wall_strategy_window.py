from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from stock_scanner.ui.windows.base_window import BaseWindow


class WallStrategyWindow(BaseWindow):
    """The Wall strategy window."""

    def __init__(self) -> None:
        super().__init__("The Wall Strategy")

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.backRequested.emit)

        title_label = QLabel("The Wall Strategy")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        status_label = QLabel("The Wall Strategy Window - Ready to implement")
        status_label.setStyleSheet("color: #ffaa00; font-size: 14px;")

        layout.addWidget(back_btn)
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addStretch()

        self.setLayout(layout)
