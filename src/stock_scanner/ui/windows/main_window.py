from typing import Optional

from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.stock_scanner.ui.windows.chart_window import ChartWindow
from src.stock_scanner.ui.windows.news_tracker_window import NewsTrackerWindow
from src.stock_scanner.ui.windows.speculation_window import SpeculationWindow
from src.stock_scanner.ui.windows.three_tier_window import ThreeTierWindow
from src.stock_scanner.ui.windows.wall_strategy_window import WallStrategyWindow


class MainWindow(QMainWindow):
    def __init__(self, entry_repo: EntryRepository, tracked_repo: TrackedTickerRepository) -> None:
        super().__init__()

        self.setWindowTitle("Stock Scanner")
        self.resize(1200, 800)

        self.chart_window = ChartWindow()
        self.three_tier_window = ThreeTierWindow()
        self.wall_window = WallStrategyWindow()
        self.speculation_window = SpeculationWindow()
        self.news_tracker_window = NewsTrackerWindow(entry_repo, tracked_repo)
        self.current_window: Optional[QWidget] = None

        central = QWidget()
        self.setCentralWidget(central)

        title = QLabel("Strategies")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.show_chart_btn = QPushButton("Show chart")
        self.show_chart_btn.clicked.connect(
            lambda: self.switch_window(self.chart_window, self.show_chart_btn)
        )
        self.show_chart_btn.setCheckable(True)

        self.the_wall = QPushButton("The wall strategy")
        self.the_wall.clicked.connect(lambda: self.switch_window(self.wall_window, self.the_wall))
        self.the_wall.setCheckable(True)

        self.three_tier = QPushButton("Three-tier strategy")
        self.three_tier.clicked.connect(lambda: self.switch_window(self.three_tier_window, self.three_tier))
        self.three_tier.setCheckable(True)

        self.speculation = QPushButton("Speculation bubble")
        self.speculation.clicked.connect(
            lambda: self.switch_window(self.speculation_window, self.speculation)
        )
        self.speculation.setCheckable(True)

        self.news_tracker = QPushButton("News tracker")
        self.news_tracker.clicked.connect(
            lambda: self.switch_window(self.news_tracker_window, self.news_tracker)
        )
        self.news_tracker.setCheckable(True)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setCheckable(True)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        self.button_group.addButton(self.show_chart_btn)
        self.button_group.addButton(self.the_wall)
        self.button_group.addButton(self.three_tier)
        self.button_group.addButton(self.speculation)
        self.button_group.addButton(self.news_tracker)
        self.button_group.addButton(self.settings_btn)

        sidebar = QVBoxLayout()
        sidebar.addWidget(title)
        sidebar.addWidget(self.show_chart_btn)
        sidebar.addWidget(self.the_wall)
        sidebar.addWidget(self.three_tier)
        sidebar.addWidget(self.speculation)
        sidebar.addWidget(self.news_tracker)
        sidebar.addStretch()
        sidebar.addWidget(self.settings_btn)

        self.sidebar_widget = QWidget()
        self.sidebar_widget.setLayout(sidebar)
        self.sidebar_widget.setStyleSheet("background-color: #252526;")

        self.window_container = QWidget()
        container_layout = QVBoxLayout(self.window_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        self.window_container.setLayout(container_layout)

        main_layout = QHBoxLayout(central)
        main_layout.addWidget(self.sidebar_widget, 1)
        main_layout.addWidget(self.window_container, 4)

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
            
            QPushButton:checked {
                background-color: #3a3a3a;
                border: 3px solid #666666;
            }
        """)

        self.show_main_menu()

    def switch_window(self, window: QWidget, button: QPushButton) -> None:
        self.show_window(window)
        button.setChecked(True)

    def show_window(self, window: QWidget) -> None:
        """Switch to a strategy window while keeping sidebar."""
        # Remove previous window
        if self.current_window:
            layout = self.window_container.layout()
            if layout:
                layout.removeWidget(self.current_window)
                self.current_window.hide()

        self.current_window = window
        layout = self.window_container.layout()
        if layout:
            layout.addWidget(window)
        window.show()

    def show_main_menu(self) -> None:
        """Return to main menu."""
        if self.current_window:
            layout = self.window_container.layout()
            if layout:
                layout.removeWidget(self.current_window)
            self.current_window.hide()
            self.current_window = None
