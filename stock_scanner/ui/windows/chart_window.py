from pathlib import Path
from typing import Optional

import pandas as pd
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from stock_scanner.ui.chart_widget import ChartWidget
from stock_scanner.ui.windows.base_window import BaseWindow


class ChartWindow(BaseWindow):
    """Chart display window for loading and viewing parquet files."""

    def __init__(self) -> None:
        self.df: Optional[pd.DataFrame] = None
        self.symbol: Optional[str] = None
        self.chart_widget: Optional[ChartWidget] = None

        super().__init__("Chart Viewer")

    def setup_ui(self) -> None:
        layout = QVBoxLayout()

        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.backRequested.emit)

        load_btn = QPushButton("Load Chart")
        load_btn.clicked.connect(self.load_chart)

        toolbar = QHBoxLayout()
        toolbar.addWidget(back_btn)
        toolbar.addWidget(load_btn)
        toolbar.addStretch()

        self.chart_widget = ChartWidget()
        self.chart_widget.setVisible(False)

        self.placeholder = QLabel("Load a parquet file to display chart")
        self.placeholder.setAlignment(self.placeholder.alignment())
        self.placeholder.setStyleSheet("color: #888888; font-size: 14px;")

        layout.addLayout(toolbar)
        layout.addWidget(self.placeholder)
        layout.addWidget(self.chart_widget)

        self.setLayout(layout)

    def load_chart(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select parquet file", "", "Parquet Files (*.parquet)"
        )

        if not file_path:
            return

        df = pd.read_parquet(file_path)

        if df.empty or "Close" not in df.columns:
            print("Invalid parquet file")
            return

        self.df = df
        self.symbol = Path(file_path).stem

        if self.chart_widget and self.symbol:
            self.chart_widget.plot(df, self.symbol)
            self.chart_widget.setVisible(True)
            self.placeholder.setVisible(False)
