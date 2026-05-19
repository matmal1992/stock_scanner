import sys
import traceback

from PySide6.QtWidgets import QApplication

from stock_scanner.ui.main_window import MainWindow


def main() -> None:
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()

        sys.exit(app.exec())

    except Exception:
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
