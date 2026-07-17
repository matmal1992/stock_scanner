import logging
import sys
import traceback
from pathlib import Path

from PySide6.QtWidgets import QApplication

from stock_scanner.download.database import Database, EntryRepository, TrackedTickerRepository
from stock_scanner.ui.main_window import MainWindow


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
    try:
        configure_logging()
        db = Database()
        db.init_db()
        entry_repo = EntryRepository(db)
        tracked_repo = TrackedTickerRepository(db)

        app = QApplication(sys.argv)
        window = MainWindow(entry_repo, tracked_repo)
        window.setMaximumSize(900, 500)
        window.show()

        sys.exit(app.exec())

    except Exception:
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
