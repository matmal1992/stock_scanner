from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from stock_scanner.ui.windows.base_window import BaseWindow


class ThreeTierWindow(BaseWindow):
    """Three-tier strategy window."""

    def __init__(self) -> None:
        super().__init__("Three-Tier Strategy")

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.backRequested.emit)

        title_label = QLabel("Three-Tier Strategy")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        status_label = QLabel("Three-Tier Strategy Window - Ready to implement")
        status_label.setStyleSheet("color: #00ff99; font-size: 14px;")

        layout.addWidget(back_btn)
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addStretch()

        self.setLayout(layout)
