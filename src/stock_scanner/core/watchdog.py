import subprocess
import sys
import time
from pathlib import Path

NORMAL_EXIT_CODE = 42


def main() -> None:
    watchdog_dir = Path(sys.executable).resolve().parent
    app_path = watchdog_dir.parent / "stock_scanner" / "stock_scanner.exe"

    while True:
        process = subprocess.Popen([str(app_path)])

        exit_code = process.wait()

        if exit_code == NORMAL_EXIT_CODE:
            break

        time.sleep(5)


if __name__ == "__main__":
    main()
