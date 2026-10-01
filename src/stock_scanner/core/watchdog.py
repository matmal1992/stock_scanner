import subprocess
import sys
import time
from pathlib import Path

from stock_scanner.core.paths import configure_logging, print_paths

NORMAL_EXIT_CODE = 42


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

        # send_telegram_alert(alert_msg)

        time.sleep(5)


if __name__ == "__main__":
    configure_logging()
    print_paths()
    main()
