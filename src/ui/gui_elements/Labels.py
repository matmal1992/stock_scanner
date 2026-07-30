# from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy


class StatusLabel(QLabel):
    def __init__(self, text: str = "") -> None:
        super().__init__(text)

        self.setWordWrap(True)

        # self.setTextInteractionFlags(
        #     Qt.TextSelectableByMouse |
        #     Qt.TextSelectableByKeyboard
        # )

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMaximumWidth(850)

    def set_error(self, text: str = "Błąd!") -> None:
        self.setText(text)
        self.setStyleSheet("color: red; font-size: 14px;")

    def set_ok(self, text: str) -> None:
        self.setText(text)
        self.setStyleSheet("color: #00ff99; font-size: 14px;")

    def set_warning(self, text: str) -> None:
        self.setText(text)
        self.setStyleSheet("color: orange; font-size: 14px;")
