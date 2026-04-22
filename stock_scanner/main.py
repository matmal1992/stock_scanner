import sys
import traceback
from pathlib import Path

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from stock_scanner.bridge import Backend
from stock_scanner.config import CONFIG_1D, CONFIG_5M, CONFIG_15M
from stock_scanner.download.downloader import run_download
from stock_scanner.profiles import PROFILE_T1, PROFILE_T2, PROFILE_T3
from stock_scanner.scanners.universal_scanner import run_scan


def main() -> None:
    try:
        app = QApplication(sys.argv)
        engine = QQmlApplicationEngine()
        backend = Backend()

        engine.rootContext().setContextProperty("backend", backend)
        qml_file = Path(__file__).resolve().parent / "ui" / "main.qml"
        engine.load(str(qml_file))

        if not engine.rootObjects():
            raise RuntimeError("QML failed to load")

        sys.exit(app.exec())

    except Exception:
        traceback.print_exc()
        input("Press Enter to exit...")


def run_3t_strategy() -> None:
    print("===== STAGE 1: DOWNLOAD first tier tickers =====")
    run_download(CONFIG_1D, "<!-- T1_DOWNLOAD -->", "first")

    print("\n===== ETAP 2: ANALIZA first tier tickers =====")
    run_scan(PROFILE_T1)

    print("\n===== STAGE 3: DOWNLOAD second tier tickers =====")
    run_download(CONFIG_15M, "<!-- T2_DOWNLOAD -->", "second")

    print("\n===== ETAP 4: ANALIZA 2nd tier tickers =====")
    run_scan(PROFILE_T2)

    print("\n===== STAGE 5: DOWNLOAD third tier tickers =====")
    run_download(CONFIG_5M, "<!-- T3_DOWNLOAD -->", "third")

    print("\n===== ETAP 6: ANALIZA third tier tickers =====")
    run_scan(PROFILE_T3)

    print("\n===== DONE =====")


if __name__ == "__main__":
    main()
