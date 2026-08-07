from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class WallStrategyWindow(QWidget):
    """The Wall strategy window."""

    def __init__(self) -> None:
        super().__init__()

    def setup_ui(self) -> None:
        title_label = QLabel("The Wall Strategy")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        status_label = QLabel("The Wall Strategy Window - Ready to implement")
        status_label.setStyleSheet("color: #ffaa00; font-size: 14px;")

        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addStretch()

        self.setLayout(layout)
