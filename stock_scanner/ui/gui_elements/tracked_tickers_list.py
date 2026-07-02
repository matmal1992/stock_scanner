from typing import Dict, List

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stock_scanner.ui.windows.news_tracker_window import NewsTrackerWindow


class TrackedTickersList(QWidget):
    def __init__(self, parent: NewsTrackerWindow) -> None:
        super().__init__()
        self.parent_window = parent
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
        buttons_box = QHBoxLayout()
        buttons_box.addWidget(self.ticker_input)
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

    def validate_input(self, ticker: str, sources: str) -> bool:
        ticker = ticker.strip().upper()
        sources = sources.strip()

        if not ticker:
            self.parent_window.notifications.set_error("Ticker nie może być pusty!")
            return False

        if not sources:
            self.parent_window.notifications.set_error("Źródła nie mogą być puste!")
            return False

        if any(t["ticker"] == ticker for t in self.ticker_list):
            self.parent_window.notifications.set_error("Ticker już jest na liście!")
            return False

        return True

    def on_add_btn_clicked(self) -> None:
        ticker = self.ticker_input.text().strip().upper()
        sources = self.sources_input.text().strip()
        is_valid = self.validate_input(ticker, sources)

        if not is_valid:
            self.parent_window.notifications.set_error("Add ticker: Nieprawidłowe dane")
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
        self.parent_window.notifications.set_ok(f"Dodano ticker: {ticker}")

        self.ticker_input.clear()
        self.sources_input.clear()

    def on_remove_btn_clicked(self) -> None:
        row = self.tracked_list.currentRow()
        if row < 0:
            self.parent_window.notifications.set_warning("Nie wybrano elementu do usunięcia")
            return

        item = self.tracked_list.takeItem(row)
        data = item.data(1)
        self.ticker_list = [t for t in self.ticker_list if t["ticker"] != data["ticker"]]
        self.parent_window.notifications.set_ok(f"Usunięto ticker: {data['ticker']}")
