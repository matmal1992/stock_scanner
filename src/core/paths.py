# import ctypes
import logging
import os
import sys
from pathlib import Path


def get_root_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def is_frozen() -> bool:
    """Czy aplikacja działa jako build PyInstaller."""
    return getattr(sys, "frozen", False)


def get_data_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parents[3] / "data"
    else:
        return get_root_dir() / "data"


def get_assets_dir() -> Path:
    if is_frozen():
        print(f"\nRoot dir: {get_root_dir()}")
        # return get_root_dir() / "build" / "dist" / "assets"
        return get_root_dir() / "assets"
    else:
        return get_root_dir() / "assets"


def application_dir() -> Path:
    if is_frozen():  # sciezka przy exe
        return Path(sys.executable).resolve().parent

    return get_root_dir()


def bundle_dir() -> Path:
    """
    Katalog zasobów dołączonych przez PyInstaller.
    """
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))

    return application_dir()


def configure_environment() -> None:
    browsers_path = bundle_dir() / "browsers"

    # ctypes.windll.user32.SetProcessDPIAware()

    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)
    logging.info(f"Playwright configured. Path: {browsers_path}")


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
