from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from stock_scanner.ui.windows.base_window import BaseWindow


class SpeculationWindow(BaseWindow):
    """Speculation bubble strategy window."""

    def __init__(self) -> None:
        super().__init__("Speculation Bubble")

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.backRequested.emit)

        title_label = QLabel("Speculation Bubble Strategy")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        status_label = QLabel("Speculation Bubble Window - Ready to implement")
        status_label.setStyleSheet("color: #ff6699; font-size: 14px;")

        layout.addWidget(back_btn)
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addStretch()

        self.setLayout(layout)
