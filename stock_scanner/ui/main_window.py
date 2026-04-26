import webbrowser
from pathlib import Path
from typing import Optional

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stock_scanner.ui.chart_widget import ChartWidget


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Stock Scanner")
        self.resize(1200, 800)

        self.df: Optional[pd.DataFrame] = None
        self.symbol: Optional[str] = None

        # === CENTRAL ===
        central = QWidget()
        self.setCentralWidget(central)

        title = QLabel("Strategies")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        show_chart_btn = QPushButton("Show chart")
        show_chart_btn.clicked.connect(self.load_chart)
        the_wall = QPushButton("The wall strategy")
        three_tier = QPushButton("Three-tier strategy")
        speculation = QPushButton("Speculation bubble")
        news_tracker = QPushButton("News tracker")
        settings_btn = QPushButton("Settings")

        sidebar = QVBoxLayout()
        sidebar.addWidget(title)
        sidebar.addWidget(show_chart_btn)
        sidebar.addWidget(the_wall)
        sidebar.addWidget(three_tier)
        sidebar.addWidget(speculation)
        sidebar.addWidget(news_tracker)
        sidebar.addStretch()
        sidebar.addWidget(settings_btn)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setStyleSheet("background-color: #252526;")

        # MAIN PANEL
        # toolbar (góra)
        self.tv_button = QPushButton("Open in TradingView")
        self.tv_button.setEnabled(False)  # na start wyłączony
        self.tv_button.clicked.connect(self.open_tradingview)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.tv_button)
        toolbar.addStretch()

        # chart area
        self.chart = ChartWidget()
        self.chart.setVisible(False)

        # placeholder
        self.placeholder = QLabel("Load a parquet file to display chart")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-size: 14px;")

        main_panel = QVBoxLayout()
        main_panel.addLayout(toolbar)
        main_panel.addWidget(self.placeholder)
        main_panel.addWidget(self.chart)

        main_layout = QHBoxLayout(central)
        main_layout.addWidget(sidebar_widget, 1)
        main_layout.addLayout(main_panel, 4)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }

            QWidget {
                background-color: #1e1e1e;
                color: #dddddd;
            }

            QPushButton {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                padding: 6px;
            }

            QPushButton:hover {
                background-color: #3a3a3a;
            }

            QPushButton:disabled {
                background-color: #222222;
                color: #777777;
            }

            QLabel {
                color: #cccccc;
            }
        """)

    def load_chart(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select parquet file", "", "Parquet Files (*.parquet)"
        )

        if not file_path:
            return

        df = pd.read_parquet(file_path)

        if df.empty or "Close" not in df.columns:
            print("Invalid data")
            return

        self.df = df
        self.symbol = Path(file_path).stem

        # pokaż wykres
        if self.symbol is None:
            return

        self.chart.plot(df, self.symbol)
        self.chart.setVisible(True)

        # ukryj placeholder
        self.placeholder.setVisible(False)

        # aktywuj TradingView
        self.tv_button.setEnabled(True)

    def open_tradingview(self) -> None:
        if not self.symbol:
            return

        symbol = self.symbol.replace("_WA", "")
        url = f"https://pl.tradingview.com/chart/?symbol=GPW%3A{symbol}"

        webbrowser.open(url)
