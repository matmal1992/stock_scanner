from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView, QListWidget


class ListWidget(QListWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setAlternatingRowColors(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._links: list[str] = []

    def set_items(self, lines: list[str], links: list[str]) -> None:
        self.clear()
        self.addItems(lines)
        self._links = links

    def add_item(self, text: str) -> None:
        self.addItem(text)

    def set_item(self, index: int, text: str) -> None:
        while self.count() <= index:
            self.addItem("")
        self.item(index).setText(text)

    def select_entry(self, index: int) -> None:
        if 0 <= index < self.count():
            self.setCurrentRow(index)

    def get_selected_entry_link(self) -> str | None:
        index = self.currentRow()
        if 0 <= index < len(self._links):
            return self._links[index]
        return None

    def make_green(self, index: int = 0) -> None:
        if item := self.item(index):
            item.setForeground(QColor("#00ff99"))

    def make_red(self, index: int = 0) -> None:
        if item := self.item(index):
            item.setForeground(QColor("red"))
