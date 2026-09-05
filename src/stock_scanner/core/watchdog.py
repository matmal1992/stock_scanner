import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

NORMAL_EXIT_CODE = 42

# Wyznaczanie katalogu bazowego względem executable lub skryptu
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent

LOGS_DIR = APP_DIR / "logs"
CRASH_DUMPS_DIR = LOGS_DIR / "dumps"
CRASH_LOG_FILE = LOGS_DIR / "crash_history.log"


def analyze_last_crash() -> str:
    """Zbiera informacje z najnowszego pliku dump (.dmp) oraz logów TXT."""
    details = []

    # 1. Odczyt z pliku logów Pythona
    if CRASH_LOG_FILE.exists():
        try:
            with open(CRASH_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_lines = "".join(lines[-15:])  # Ostatnie 15 linijek logu
                    details.append(f"📄 **Ostatni wyjątek z logu:**\n```\n{last_lines}\n```")
        except Exception as e:
            details.append(f"Nie udało się odczytać pliku logu: {e}")

    # 2. Wykrywanie najnowszego Minidumpa
    if CRASH_DUMPS_DIR.exists():
        dumps = sorted(CRASH_DUMPS_DIR.glob("*.dmp"), key=os.path.getmtime, reverse=True)
        if dumps:
            latest_dump = dumps[0]
            # Sprawdzenie czy plik powiązany jest z ostatnim crashem (utworzony w ciągu ostatnich 30s)
            if time.time() - latest_dump.stat().st_mtime < 30:
                dump_info = parse_minidump_basic(latest_dump)
                details.append(f"📦 **Wykryto plik Minidump (.dmp):** `{latest_dump.name}`\n{dump_info}")

    if not details:
        return "Nie znaleziono szczegółowych logów błędu (prawdopodobnie wymuszone zamknięcie procesu)."

    return "\n\n".join(details)


def parse_minidump_basic(dump_path: Path) -> str:
    """Podstawowa analiza pliku minidump (nagłówki) bez zewnętrznych zależności."""
    try:
        size_kb = dump_path.stat().st_size / 1024
        creation_time = datetime.fromtimestamp(dump_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return f"- Rozmiar: {size_kb:.2f} KB\n- Utworzono: {creation_time}"
    except Exception as e:
        return f"Błąd podczas analizy pliku dump: {e}"


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
    main()
