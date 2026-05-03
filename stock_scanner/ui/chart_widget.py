import pandas as pd
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget


class ChartWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout = QVBoxLayout()
        toolbar_layout = QHBoxLayout()
        for action in self.toolbar.actions():
            if action.isSeparator():
                continue
            button = QPushButton(action.text())
            button.clicked.connect(action.trigger)
            button.setEnabled(action.isEnabled())

            def update_enabled(btn=button, act=action):  # type: ignore[no-untyped-def]
                btn.setEnabled(act.isEnabled())

            action.changed.connect(update_enabled)
            button.setStyleSheet(
                "QPushButton { background-color: #1e1e1e; color: white; border: 1px solid #555; padding: 5px; }"
                "QPushButton:hover { background-color: #333333; }"
                "QPushButton:pressed { background-color: #444444; }"
                "QPushButton:disabled { color: #888; }"
            )
            toolbar_layout.addWidget(button)
        layout.addLayout(toolbar_layout)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.ax = self.figure.add_subplot(111)

    def plot(self, df: pd.DataFrame, title: str = "Chart") -> None:
        self.ax.clear()

        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)

        # Check if OHLC data is available
        required_cols = {"Open", "High", "Low", "Close"}
        if not required_cols.issubset(df.columns):
            # Fallback to line chart if OHLC data is not available
            self.ax.plot(df.index, df["Close"], linewidth=1.5, color="#00ff99")
            self.ax.set_title(f"{title} (Line Chart)")
        else:
            self._plot_candlestick(df)
            self.ax.set_title(f"{title} (Candlestick)")

        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Price")
        self.ax.grid(True, alpha=0.3)
        self.ax.tick_params(axis="x", rotation=45)

        self.figure.tight_layout()
        self.canvas.draw()

    def _plot_candlestick(self, df: pd.DataFrame) -> None:
        """Plot candlestick chart."""
        width = 0.6

        for i, (idx, row) in enumerate(df.iterrows()):
            open_price = row["Open"]
            high_price = row["High"]
            low_price = row["Low"]
            close_price = row["Close"]

            if close_price >= open_price:
                color = "#00ff99"  # Green for up
                body_height = close_price - open_price
                body_bottom = open_price
            else:
                color = "#ff4444"  # Red for down
                body_height = open_price - close_price
                body_bottom = close_price

            self.ax.vlines(i, low_price, high_price, colors=color, linewidth=0.5)

            if body_height == 0:
                self.ax.hlines(open_price, i - width / 2, i + width / 2, colors=color, linewidth=1)
            else:
                rect = Rectangle(
                    (i - width / 2, body_bottom),
                    width,
                    body_height,
                    facecolor=color,
                    edgecolor=color,
                    linewidth=0.5,
                )
                self.ax.add_patch(rect)

        all_dates = df.index
        self.ax.set_xlim(-1, len(df))
        self.ax.set_xticks(range(len(df)))
        step = max(1, len(df) // 10)
        self.ax.set_xticklabels(
            [all_dates[i].strftime("%Y-%m-%d") if i % step == 0 else "" for i in range(len(df))],
            rotation=45,
        )
