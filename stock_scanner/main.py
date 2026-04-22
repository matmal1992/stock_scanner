import sys
import traceback
from pathlib import Path

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from stock_scanner.bridge import Backend


def main() -> None:
    try:
        app = QApplication(sys.argv)
        engine = QQmlApplicationEngine()
        backend = Backend()

        engine.rootContext().setContextProperty("bridge", backend)
        qml_file = Path(__file__).resolve().parent / "ui" / "main.qml"
        engine.load(str(qml_file))

        if not engine.rootObjects():
            raise RuntimeError("QML failed to load")

        sys.exit(app.exec())

    except Exception:
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
