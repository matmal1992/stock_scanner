from typing import Sequence

from PySide6.QtWidgets import QListWidget


class ListWidget(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self._ids: list[str | None] = []

    def set_items(self, items: Sequence[tuple[str, str | None]]) -> None:
        self.clear()
        self._ids = []

        for text, entry_id in items:
            self.addItem(text)
            self._ids.append(entry_id)

    def get_selected_id(self) -> str | None:
        index = self.currentRow()
        if 0 <= index < len(self._ids):
            return self._ids[index]
        return None
