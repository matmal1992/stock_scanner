import logging
import os
import subprocess
import sys
import time
from pathlib import Path

from minidump.minidumpfile import MinidumpFile
from stock_scanner.core.paths import application_dir, configure_logging, print_paths

logger = logging.getLogger(__name__)

NORMAL_EXIT_CODE = 42

CRASH_DUMPS_DIR = Path("C:/StockScannerDumps")
CRASH_LOG_FILE = application_dir() / "crash_history.log"


def parse_minidump_detailed(dump_path: Path) -> str:
    """Odczytuje szczegółowe informacje z pliku .dmp przy użyciu biblioteki minidump."""

    try:
        mf = MinidumpFile.parse(str(dump_path))
        info_lines = []

        fault_addr: int | None = None

        # 1. Informacje o wyjątku (Exception Stream via ExceptionList)
        if mf.exception and mf.exception.exception_records:
            # Pobieramy pierwszy/główny rekord wyjątku z listy
            exc_record = mf.exception.exception_records[0]

            # W zależności od wersji biblioteki, rekord może zawierać słownik lub obiekty rekordów
            exc_code = getattr(exc_record, "ExceptionCode", None)
            exc_addr = getattr(exc_record, "ExceptionAddress", None)

            if exc_code is not None:
                info_lines.append(f"- **Kod wyjątku (Exception Code):** `0x{exc_code:08X}`")
            if exc_addr is not None:
                fault_addr = exc_addr
                info_lines.append(f"- **Adres awarii (Fault Address):** `0x{exc_addr:016X}`")

        # 2. Informacje o systemie (System Info Stream)
        if mf.sysinfo:
            sys_info = mf.sysinfo
            os_ver = f"{sys_info.MajorVersion}.{sys_info.MinorVersion}.{sys_info.BuildNumber}"
            architecture = sys_info.ProcessorArchitecture

            if architecture is not None:
                architecture_name = architecture.name
            else:
                architecture_name = "Unknown"

            info_lines.append(f"- **Architektura / OS:** {architecture_name} | Win {os_ver}")

        # 3. Lista wątków (Thread List)
        if mf.threads and hasattr(mf.threads, "threads"):
            info_lines.append(f"- **Liczba aktywnych wątków:** {len(mf.threads.threads)}")

        # 4. Identyfikacja uszkodzonego modułu (.dll / .exe)
        if mf.modules and fault_addr is not None:
            fault_module = None
            for mod in mf.modules.modules:
                if mod.baseaddress <= fault_addr <= (mod.baseaddress + mod.size):
                    fault_module = mod.name
                    break

            if fault_module:
                info_lines.append(f"- **Uszkodzony moduł:** `{fault_module}`")

        if not info_lines:
            return "- Plik minidump nie zawiera standardowych strumieni błędu."

        return "\n".join(info_lines)

    except Exception as e:
        return f"- Błąd parsowania pliku .dmp: `{e}`"


def analyze_last_crash() -> str:
    """Zbiera informacje z najnowszego pliku dump (.dmp) oraz logów TXT."""
    details = []

    # 1. Odczyt z pliku logów Pythona
    if CRASH_LOG_FILE.exists():
        try:
            with open(CRASH_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_lines = "".join(lines[-15:])
                    details.append(f"📄 **Ostatni wyjątek Python z logu:**\n```\n{last_lines}\n```")
        except Exception as e:
            details.append(f"Nie udało się odczytać pliku logu: {e}")

    # 2. Wykrywanie najnowszego Minidumpa (.dmp)
    if CRASH_DUMPS_DIR.exists():
        dumps = sorted(CRASH_DUMPS_DIR.glob("*.dmp"), key=os.path.getmtime, reverse=True)
        if dumps:
            latest_dump = dumps[0]
            # Sprawdzenie, czy dump powstał w trakcie ostatniej awarii (w ciągu 60 sekund)
            if time.time() - latest_dump.stat().st_mtime < 60:
                dump_analysis = parse_minidump_detailed(latest_dump)
                details.append(f"📦 **Analiza pliku Minidump (`{latest_dump.name}`):**\n{dump_analysis}")

    if not details:
        return "Nie znaleziono szczegółowych logów błędu."

    return "\n\n".join(details)


# def send_telegram_alert(message: str) -> None:
#     """Pomocnicza funkcja do wysyłania alertu z poziomu Watchdoga."""
#     try:
#         from src.stock_scanner.core.telegram import send_telegram_alert as send_alert

#         send_alert(message)
#     except Exception as e:
#         print(f"Błąd wysyłania alertu Telegram przez Watchdoga: {e}")


def main() -> None:
    watchdog_dir = Path(sys.executable).resolve().parent
    app_path = watchdog_dir.parent / "stock_scanner" / "stock_scanner.exe"

    # W trybie deweloperskim (skrypt python):
    if not app_path.exists():
        app_path = Path("main.py")

    while True:
        cmd = [str(app_path)] if app_path.suffix == ".exe" else [sys.executable, str(app_path)]
        process = subprocess.Popen(cmd)

        exit_code = process.wait()

        print(f"Stock Scanner zakończył się z kodem: {exit_code}")

        if exit_code == NORMAL_EXIT_CODE:
            print("Normalne zamknięcie aplikacji.")
            break

        print("Nieprawidłowe zakończenie — zbieranie informacji o awarii...")
        crash_report = analyze_last_crash()

        alert_msg = f"""⚠️ **Watchdog:** Aplikacja padła (Exit Code: {exit_code}).\n\n{crash_report}\n\n
        🔄 Restart za 5 sekund..."""
        print(alert_msg)
        # send_telegram_alert(alert_msg)

        time.sleep(5)


if __name__ == "__main__":
    configure_logging()
    print_paths()
    main()
