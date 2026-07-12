from typing import Dict, List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stock_scanner.download.database import TrackedTickerRepository


class TrackedTickersList(QWidget):
    notify = Signal(str, str)

    def __init__(self, repo: TrackedTickerRepository) -> None:
        super().__init__()
        self.repo = repo
        self.set_up_widgets()
        self.set_up_layout()
        self.load_from_db()

    def load_from_db(self) -> None:
        rows = self.repo.get_all()

        for row in rows:
            data = {
                "ticker_symbol": row["ticker_symbol"],
                "ticker_name": row["ticker_name"],
                "sources": row["sources"],
            }
            self.ticker_list.append(data)

            item_text = f"{row['ticker_symbol']} - {row['ticker_name']} - {row['sources']}"
            item = QListWidgetItem(item_text)
            item.setData(1, data)

            self.tracked_list.addItem(item)

    def set_up_widgets(self) -> None:
        self.ticker_list: List[Dict[str, str]] = []
        self.ticker_symbol_input = QLineEdit()
        self.ticker_symbol_input.setFixedWidth(100)
        self.ticker_symbol_input.setPlaceholderText("Ticker")
        self.ticker_name_input = QLineEdit()
        self.ticker_name_input.setPlaceholderText("Full name")
        self.sources_input = QLineEdit()
        self.sources_input.setPlaceholderText("Sources")
        self.tracked_list = QListWidget()
        self.add_btn = QPushButton("Add to tracked")
        self.add_btn.clicked.connect(self.on_add_btn_clicked)
        self.remove_btn = QPushButton("Remove selected")
        self.remove_btn.clicked.connect(self.on_remove_btn_clicked)

    def set_up_layout(self) -> None:
        buttons_box = QHBoxLayout()
        buttons_box.addWidget(self.ticker_symbol_input)
        buttons_box.addSpacing(10)
        buttons_box.addWidget(self.ticker_name_input)
        buttons_box.addSpacing(10)
        buttons_box.addWidget(self.sources_input)
        buttons_box.addSpacing(60)
        buttons_box.addWidget(self.add_btn)
        buttons_box.addSpacing(10)
        buttons_box.addWidget(self.remove_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(buttons_box)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.tracked_list)
        self.setLayout(main_layout)

    def validate_input(self, ticker: str, ticker_name: str, sources: str) -> bool:
        ticker = ticker.strip().upper()
        sources = sources.strip()

        if not ticker:
            self.notify.emit("Ticker nie może być pusty!", "error")
            return False

        if not sources:
            self.notify.emit("Źródła nie mogą być puste!", "error")
            return False

        if any(t["ticker_symbol"] == ticker for t in self.ticker_list):
            self.notify.emit("Ticker już jest na liście!", "error")
            return False

        return True

    def on_add_btn_clicked(self) -> None:
        ticker_symbol = self.ticker_symbol_input.text().strip().upper()
        ticker_name = self.ticker_name_input.text().strip()
        sources = self.sources_input.text().strip()

        if not self.validate_input(ticker_symbol, ticker_name, sources):
            self.notify.emit("Nie wypełniłeś wszystkich pól!", "error")
            return

        success = self.repo.save(ticker_symbol=ticker_symbol, ticker_name=ticker_name, sources=sources)
        if not success:
            self.notify.emit("Nie udało się zapisać tickera!", "error")
            return

        data = {
            "ticker_symbol": ticker_symbol,
            "ticker_name": ticker_name,
            "sources": sources,
        }

        self.ticker_list.append(data)

        item_text = f"{ticker_symbol} - {ticker_name} - {sources}"
        item = QListWidgetItem(item_text)
        item.setData(1, data)

        self.tracked_list.addItem(item)

        self.ticker_symbol_input.clear()
        self.ticker_name_input.clear()
        self.sources_input.clear()

    def on_remove_btn_clicked(self) -> None:
        row = self.tracked_list.currentRow()
        if row < 0:
            return

        item = self.tracked_list.item(row)
        data = item.data(1)

        success = self.repo.remove(data["ticker_symbol"])
        if not success:
            return

        self.tracked_list.takeItem(row)

        self.ticker_list = [t for t in self.ticker_list if t["ticker_symbol"] != data["ticker_symbol"]]
        self.notify.emit(f"Usunięto ticker: {data['ticker_symbol']}", "neutral")
