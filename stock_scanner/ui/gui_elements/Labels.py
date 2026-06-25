from PySide6.QtWidgets import QLabel

class StatusLabel(QLabel):
    def set_error(self, text="Błąd!"):
        self.setText(text)
        self.setStyleSheet("color: red; font-size: 14px;")

    def set_ok(self, text):
        self.setText(text)
        self.setStyleSheet("color: #00ff99; font-size: 14px;")

    def set_warning(self, text):
        self.setText(text)
        self.setStyleSheet("color: orange; font-size: 14px;")