import sys
import traceback
from types import TracebackType
from typing import Type

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.stock_scanner.core.paths import configure_environment, configure_logging, get_assets_dir
from src.stock_scanner.core.telegram import send_telegram_alert
from src.stock_scanner.download.database import Database
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.stock_scanner.ui.windows.main_window import MainWindow


def main() -> None:
    sys.excepthook = handle_exception
    configure_logging()
    configure_environment()
    send_telegram_alert("🟢 Stock Scanner uruchomiony.")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    db = Database()
    db.init_db()
    entry_repo = EntryRepository(db)
    tracked_repo = TrackedTickerRepository(db)
    window = MainWindow(entry_repo, tracked_repo)
    window.setWindowFlag(Qt.WindowType.Tool, True)

    tray_icon = QSystemTrayIcon()
    tray_icon.setIcon(QIcon(f"{get_assets_dir()}/icon.ico"))
    tray_icon.setToolTip("Stock Scanner")
    tray_menu = QMenu()
    show_action = QAction("Pokaż", tray_menu)
    hide_action = QAction("Ukryj", tray_menu)
    quit_action = QAction("Zamknij", tray_menu)

    tray_menu.addAction(show_action)
    tray_menu.addAction(hide_action)
    tray_menu.addSeparator()
    tray_menu.addAction(quit_action)
    tray_icon.setContextMenu(tray_menu)

    def show_window() -> None:
        window.show()
        window.showNormal()
        window.activateWindow()
        window.raise_()

    def hide_window() -> None:
        window.hide()

    def quit_application() -> None:
        send_telegram_alert("🛑 Stock Scanner został zamknięty.")
        tray_icon.hide()
        app.quit()

    show_action.triggered.connect(show_window)
    hide_action.triggered.connect(hide_window)
    quit_action.triggered.connect(quit_application)

    tray_icon.activated.connect(
        lambda reason: show_window() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None
    )

    tray_icon.show()
    window.hide()
    window.start_news_strategy()

    try:
        exit_code = app.exec()
    except Exception:
        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)


def handle_exception(
    exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None
) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    traceback.print_exception(exc_type, exc_value, exc_traceback)

    try:
        send_telegram_alert(f"💥 Stock Scanner zakończył działanie przez wyjątek:\n{exc_value}")
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
