import pandas as pd
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget


class ChartWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.ax = self.figure.add_subplot(111)

    def plot(self, df: pd.DataFrame, title: str = "Chart") -> None:
        self.ax.clear()

        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)

        self.ax.plot(df.index, df["Close"], linewidth=1.5)

        self.ax.set_title(title)
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Close")
        self.ax.grid(True)

        self.figure.tight_layout()
        self.canvas.draw()
