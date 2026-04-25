from pathlib import Path

import pandas as pd
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

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        sidebar = QVBoxLayout()

        title = QLabel("Strategies")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        btn_load = QPushButton("Show chart")
        btn_load.clicked.connect(self.load_chart)

        btn_3t = QPushButton("3T strategy")
        btn_3t.clicked.connect(self.run_3t_strategy)

        sidebar.addWidget(title)
        sidebar.addWidget(btn_load)
        sidebar.addWidget(btn_3t)
        sidebar.addStretch()

        self.chart = ChartWidget()

        main_layout.addLayout(sidebar, 1)
        main_layout.addWidget(self.chart, 4)

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

        title = Path(file_path).stem
        self.chart.plot(df, title)

    def run_3t_strategy(self) -> None:
        print("Run 3T strategy here")
