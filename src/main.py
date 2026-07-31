import logging
import os
import sys
import traceback
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.download.database import Database
from src.strategies.news_tracker.entry_repo import EntryRepository
from src.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.ui.windows.main_window import MainWindow


def get_log_file_path() -> Path:
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(sys.argv[0]).resolve().parent
    return base_dir / "stock_scanner.log"


def configure_logging() -> None:
    log_file = get_log_file_path()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info(f"Logging initialized. Log file: {log_file}")


def main() -> None:
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", "")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(base_path, "browsers")
    else:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "browsers"

    configure_logging()
    app = QApplication(sys.argv)
    db = Database()
    db.init_db()
    entry_repo = EntryRepository(db)
    tracked_repo = TrackedTickerRepository(db)
    window = MainWindow(entry_repo, tracked_repo)
    window.setMaximumSize(900, 500)
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
