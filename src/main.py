import sys
import traceback

from PySide6.QtWidgets import QApplication

from src.stock_scanner.core.paths import configure_environment, configure_logging, print_paths
from src.stock_scanner.download.database import Database
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.stock_scanner.ui.windows.main_window import MainWindow


def main() -> None:
    configure_logging()
    configure_environment()
    print_paths()

    app = QApplication(sys.argv)
    db = Database()
    db.init_db()
    entry_repo = EntryRepository(db)
    tracked_repo = TrackedTickerRepository(db)
    window = MainWindow(entry_repo, tracked_repo)
    window.showMaximized()
    window.show()
    window.start_news_strategy()

    exit_code = 0
    try:
        exit_code = app.exec()
    except Exception:
        traceback.print_exc()
        exit_code = 1
    finally:
        input("Press Enter to exit...")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
