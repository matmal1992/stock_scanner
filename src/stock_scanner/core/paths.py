# import ctypes
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_root_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent.parent.parent.parent
    else:
        return Path(__file__).resolve().parent.parent.parent.parent


def get_data_dir() -> Path:
    return get_root_dir() / "data"


def get_browser_dir() -> Path:
    return get_root_dir() / "browsers"


def get_assets_dir() -> Path:
    if getattr(sys, "frozen", False):
        return application_dir() / "_internal" / "assets"
    else:
        return get_root_dir() / "assets"


def application_dir() -> Path:
    if getattr(sys, "frozen", False):  # sciezka przy exe
        return Path(sys.executable).resolve().parent

    return get_root_dir()


def internal_dir() -> Path:
    """
    Katalog zasobów dołączonych przez PyInstaller.
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))

    return application_dir()


def configure_environment() -> None:
    browsers_path = internal_dir() / "browsers"

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


def print_paths() -> None:
    print(f"get_root_dir: {get_root_dir()}")
    print(f"get_assets_dir: {get_assets_dir()}")
    print(f"application_dir: {application_dir()}")
    print(f"get_log_file_path: {get_log_file_path()}")
    print(f"internal_dir: {internal_dir()}")
    print(f"get_data_dir: {get_data_dir()}")
    print(f"get_browser_dir: {get_browser_dir()}")
    # print(f"watchdog_dir: {internal_dir()}")

    logger.info(f"get_root_dir: {get_root_dir()}")
    logger.info(f"get_assets_dir: {get_assets_dir()}")
    logger.info(f"application_dir: {application_dir()}")
    logger.info(f"get_log_file_path: {get_log_file_path()}")
    logger.info(f"internal_dir: {internal_dir()}")
    logger.info(f"get_data_dir: {get_data_dir()}")
    logger.info(f"get_browser_dir: {get_browser_dir()}")
    # logger.info(f"watchdog_dir: {internal_dir()}")
