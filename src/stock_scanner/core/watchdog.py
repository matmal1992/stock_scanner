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

        print(f"Stock Scanner zakończył się z kodem: {exit_code}")

        if exit_code == NORMAL_EXIT_CODE:
            print("Normal exit code")
            break

        print("Nieprawidłowe zakończenie - restart za 5 sekund")
        time.sleep(5)


if __name__ == "__main__":
    main()
