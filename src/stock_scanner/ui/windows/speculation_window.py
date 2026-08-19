from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SpeculationWindow(QWidget):
    """Speculation bubble strategy window."""

    def __init__(self) -> None:
        super().__init__()

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        title_label = QLabel("Speculation Bubble Strategy")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        status_label = QLabel("Speculation Bubble Window - Ready to implement")
        status_label.setStyleSheet("color: #ff6699; font-size: 14px;")

        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addStretch()

        self.setLayout(layout)
