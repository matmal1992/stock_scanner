from typing import Optional

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from stock_scanner.ui.windows.chart_window import ChartWindow
from stock_scanner.ui.windows.news_tracker_window import NewsTrackerWindow
from stock_scanner.ui.windows.speculation_window import SpeculationWindow
from stock_scanner.ui.windows.three_tier_window import ThreeTierWindow
from stock_scanner.ui.windows.wall_strategy_window import WallStrategyWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Stock Scanner")
        self.resize(1200, 800)

        # Initialize all windows (state preservation)
        self.chart_window = ChartWindow()
        self.three_tier_window = ThreeTierWindow()
        self.wall_window = WallStrategyWindow()
        self.speculation_window = SpeculationWindow()
        self.news_tracker_window = NewsTrackerWindow()

        # Connect back buttons
        self.chart_window.backRequested.connect(self.show_main_menu)
        self.three_tier_window.backRequested.connect(self.show_main_menu)
        self.wall_window.backRequested.connect(self.show_main_menu)
        self.speculation_window.backRequested.connect(self.show_main_menu)
        self.news_tracker_window.backRequested.connect(self.show_main_menu)

        self.current_window: Optional[QWidget] = None

        # === CENTRAL ===
        central = QWidget()
        self.setCentralWidget(central)

        # === SIDEBAR ===
        title = QLabel("Strategies")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        show_chart_btn = QPushButton("Show chart")
        show_chart_btn.clicked.connect(lambda: self.show_window(self.chart_window))

        the_wall = QPushButton("The wall strategy")
        the_wall.clicked.connect(lambda: self.show_window(self.wall_window))

        three_tier = QPushButton("Three-tier strategy")
        three_tier.clicked.connect(lambda: self.show_window(self.three_tier_window))

        speculation = QPushButton("Speculation bubble")
        speculation.clicked.connect(lambda: self.show_window(self.speculation_window))

        news_tracker = QPushButton("News tracker")
        news_tracker.clicked.connect(lambda: self.show_window(self.news_tracker_window))

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

        self.sidebar_widget = QWidget()
        self.sidebar_widget.setLayout(sidebar)
        self.sidebar_widget.setStyleSheet("background-color: #252526;")

        # === WINDOW CONTAINER ===
        self.window_container = QWidget()
        container_layout = QVBoxLayout(self.window_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        self.window_container.setLayout(container_layout)

        # === MAIN LAYOUT ===
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
        """)

        # Show main menu on start
        self.show_main_menu()

    def show_window(self, window: QWidget) -> None:
        """Switch to a strategy window while keeping sidebar."""
        # Remove previous window
        if self.current_window:
            layout = self.window_container.layout()
            if layout:
                layout.removeWidget(self.current_window)
                self.current_window.hide()

        # Add new window
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
