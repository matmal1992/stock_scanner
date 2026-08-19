from PySide6.QtWidgets import QFrame


class HLine(QFrame):
    def __init__(self, name: str = "common_line", height: int = 1) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setObjectName(name)
        self.setFixedHeight(height)
        self.setContentsMargins(0, 0, 0, 0)


class VLine(QFrame):
    def __init__(self, name: str = "common_line", width: int = 1) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.VLine)
        self.setFrameShadow(QFrame.Shadow.Plain)
        self.setObjectName(name)
        self.setFixedWidth(width)
        self.setContentsMargins(0, 0, 0, 0)
