import sys
import traceback

from PySide6.QtWidgets import QApplication

from src.core.paths import configure_environment, configure_logging
from src.download.database import Database
from src.strategies.news_tracker.entry_repo import EntryRepository
from src.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.ui.windows.main_window import MainWindow


def main() -> None:
    configure_logging()
    configure_environment()

    app = QApplication(sys.argv)
    db = Database()
    db.init_db()
    entry_repo = EntryRepository(db)
    tracked_repo = TrackedTickerRepository(db)
    window = MainWindow(entry_repo, tracked_repo)
    window.showMaximized()
    window.show()

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
