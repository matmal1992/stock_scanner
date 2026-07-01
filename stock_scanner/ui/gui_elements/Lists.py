from typing import Dict, List, Sequence

from PySide6.QtWidgets import (
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


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


class TrackedTickersList(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.set_up_widgets()
        self.set_up_layout()

    def set_up_widgets(self) -> None:
        self.ticker_list: List[Dict[str, str]] = []
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("Ticker")
        self.sources_input = QLineEdit()
        self.sources_input.setPlaceholderText("Sources")
        self.tracked_list = QListWidget()
        self.add_btn = QPushButton("Add to tracked")
        self.add_btn.clicked.connect(self.on_add_btn_clicked)
        self.remove_btn = QPushButton("Remove selected")
        self.remove_btn.clicked.connect(self.on_remove_btn_clicked)

    def set_up_layout(self) -> None:
        layout = QVBoxLayout()
        layout.addWidget(self.ticker_input)
        layout.addWidget(self.sources_input)
        layout.addWidget(self.add_btn)
        layout.addWidget(self.tracked_list)
        self.setLayout(layout)

    def validate_input(self, ticker: str, sources: str) -> bool:
        ticker = ticker.strip().upper()
        sources = sources.strip()

        if not ticker:
            return False

        if not sources:
            return False

        if any(t["ticker"] == ticker for t in self.ticker_list):
            return False

        return True

    def on_add_btn_clicked(self) -> None:
        ticker = self.ticker_input.text().strip().upper()
        sources = self.sources_input.text().strip()
        is_valid = self.validate_input(ticker, sources)

        if not is_valid:
            print("Nieprawidłowe dane")
            return

        data = {
            "ticker": ticker,
            "sources": sources,
        }

        self.ticker_list.append(data)

        item_text = f"{ticker} - {sources}"
        item = QListWidgetItem(item_text)

        # przechowujemy dane w itemie
        item.setData(1, data)
        self.tracked_list.addItem(item)

        self.ticker_input.clear()
        self.sources_input.clear()

    def on_remove_btn_clicked(self) -> None:
        row = self.tracked_list.currentRow()
        if row < 0:
            return

        item = self.tracked_list.takeItem(row)
        data = item.data(1)
        self.ticker_list = [t for t in self.ticker_list if t["ticker"] != data["ticker"]]
