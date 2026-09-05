import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from types import FrameType, TracebackType
from typing import Type

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.stock_scanner.core.paths import (
    application_dir,
    configure_environment,
    configure_logging,
    get_assets_dir,
)
from src.stock_scanner.core.telegram import send_telegram_alert
from src.stock_scanner.download.database import Database
from src.stock_scanner.strategies.news_tracker.entry_repo import EntryRepository
from src.stock_scanner.strategies.news_tracker.tracked_ticker_repo import TrackedTickerRepository
from src.stock_scanner.ui.windows.main_window import MainWindow

NORMAL_EXIT_CODE = 42
LOGS_DIR = Path(application_dir() / "logs")
CRASH_DUMPS_DIR = LOGS_DIR / "dumps"


def setup_crash_handling() -> None:
    """Konfiguruje tworzenie plików .dmp przy krytycznych crashach C++/Natywnych."""
    LOGS_DIR.mkdir(exist_ok=True)
    CRASH_DUMPS_DIR.mkdir(exist_ok=True)

    if sys.platform == "win32":
        import ctypes
        import signal

        def write_minidump() -> None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_file = CRASH_DUMPS_DIR / f"crash_{timestamp}.dmp"

            try:
                dbghelp = ctypes.windll.dbghelp
                kernel32 = ctypes.windll.kernel32
                current_process = kernel32.GetCurrentProcess()
                current_process_id = kernel32.GetCurrentProcessId()

                with open(dump_file, "wb") as f:
                    # MiniDumpWithFullMemoryInfo / Normal MiniDump flags (0x00000000)
                    success = dbghelp.MiniDumpWriteDump(
                        current_process,
                        current_process_id,
                        f.fileno(),
                        0x00000000,  # MiniDumpNormal
                        None,
                        None,
                        None,
                    )
                    if success:
                        logging.critical(f"Pomyślnie zapisano plik minidump: {dump_file}")
            except Exception as e:
                logging.error(f"Nie udało się wygenerować minidumpa: {e}")

        def handle_fatal_signal(sig: int, frame: FrameType | None) -> None:
            logging.critical(f"Otrzymano krytyczny sygnał systemowy: {sig}")
            write_minidump()
            sys.exit(1)

        # Rejestracja sygnałów naruszenia pamięci i awarii natywnych
        signal.signal(signal.SIGSEGV, handle_fatal_signal)
        signal.signal(signal.SIGABRT, handle_fatal_signal)
        signal.signal(signal.SIGFPE, handle_fatal_signal)


def setup_file_logger() -> None:
    """Dodatkowa obsługa zapisu wyjątków do dedykowanego pliku logów crashy."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    crash_log_file = LOGS_DIR / "crash_history.log"
    handler = logging.FileHandler(crash_log_file, encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger = logging.getLogger("CrashLogger")
    logger.setLevel(logging.ERROR)
    logger.addHandler(handler)


def handle_exception(
    exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None
) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Sformatuj pełny traceback
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    # 1. Zapis do pliku logów
    crash_logger = logging.getLogger("CrashLogger")
    crash_logger.error(f"Nieobsłużony wyjątek Python:\n{tb_text}")

    # 2. Wypisanie na stderr
    traceback.print_exception(exc_type, exc_value, exc_traceback)

    # 3. Alert Telegram
    try:
        send_telegram_alert(
            f"""💥 **Stock Scanner Crash (Python Exception)**:\n```{exc_value}```\n
            Zobacz plik logów po więcej szczegółów."""
        )
    except Exception:
        traceback.print_exc()


def main() -> None:
    setup_file_logger()
    setup_crash_handling()
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
        tray_icon.hide()
        app.exit(NORMAL_EXIT_CODE)

    show_action.triggered.connect(show_window)
    hide_action.triggered.connect(hide_window)
    quit_action.triggered.connect(quit_application)

    tray_icon.activated.connect(
        lambda reason: show_window() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None
    )

    tray_icon.show()
    window.hide()

    try:
        exit_code = app.exec()
    except Exception as e:
        handle_exception(type(e), e, e.__traceback__)
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
