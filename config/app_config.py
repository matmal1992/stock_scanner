import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.stock_scanner.core.paths import get_root_dir

BASE_DIR = get_root_dir()
CONFIG_PATH = BASE_DIR / "config" / "config.json"

# https://api.telegram.org/bot<chat_token>/getUpdates
# https://api.telegram.org/bot<TWOJ_TOKEN>/getChat?chat_id=<CHAT_ID>


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Nie znaleziono pliku konfiguracyjnego: {CONFIG_PATH}")

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Nieprawidłowy format JSON w pliku: {CONFIG_PATH}. Wiersz {e.lineno}, kolumna {e.colno}: {e.msg}"
        ) from e

    except OSError as e:
        raise OSError(f"Nie udało się odczytać pliku konfiguracyjnego: {CONFIG_PATH}. Przyczyna: {e}") from e

    if not isinstance(config, dict):
        raise ValueError(f"Plik konfiguracyjny musi zawierać obiekt JSON: {CONFIG_PATH}")

    validate_json(config)

    return config


def validate_json(value: Any, path: str = "") -> None:
    """Sprawdza rekurencyjnie, czy JSON nie zawiera pustych stringów."""
    if isinstance(value, str):
        if not value.strip():
            raise ValueError(f"Pusta wartość tekstowa w konfiguracji: {path or '<root>'} ({CONFIG_PATH})")

    elif isinstance(value, dict):
        for key, nested_value in value.items():
            if isinstance(key, str) and not key.strip():
                raise ValueError(f"Pusty klucz w konfiguracji: {CONFIG_PATH}")

            validate_json(nested_value, f"{path}.{key}" if path else str(key))

    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_json(item, f"{path}[{index}]")


@dataclass(frozen=True)
class ConfigKeys:
    """Klasa przechowująca konfigurację aplikacji (niemutowalna)."""

    alert_chat_token: str
    state_chat_token: str
    debug_chat_token: str

    alert_chat_id: str
    state_chat_id: str
    debug_chat_id: str

    state_chat_pinned_message_id: str
    llm_pinned_error_msg_id: str
    llm_pinned_error_screen_msg_id: str
    llm_error_log_file_id: str

    @classmethod
    def from_json(cls) -> "ConfigKeys":
        """Fabryka ładująca konfigurację z pliku JSON i mapująca ją na dataclass."""
        config = load_config()

        return cls(
            alert_chat_token=str(config["alert_chat_token"]),
            state_chat_token=str(config["state_chat_token"]),
            debug_chat_token=str(config["debug_chat_token"]),
            alert_chat_id=str(config["alert_chat_id"]),
            state_chat_id=str(config["state_chat_id"]),
            debug_chat_id=str(config["debug_chat_id"]),
            state_chat_pinned_message_id=str(config["state_chat_pinned_message_id"]),
            llm_pinned_error_msg_id=str(config["llm_pinned_error_msg_id"]),
            llm_pinned_error_screen_msg_id=str(config["llm_pinned_error_screen_msg_id"]),
            llm_error_log_file_id=str(config["llm_error_log_file_id"]),
        )


@dataclass
class DownloadConfig:
    interval: str
    period_days: int
    data_folder: str
    downloaded_tickers_file: str
    tickers_to_download: str
    last_update_file: str
    interval_minutes: int

    @property
    def data_dir(self) -> Path:
        return BASE_DIR / "data" / "parquet" / self.data_folder

    @property
    def tickers_path(self) -> Path:
        return BASE_DIR / "data" / "txt" / self.downloaded_tickers_file

    @property
    def to_download(self) -> Path:
        return BASE_DIR / "data" / "txt" / self.tickers_to_download

    @property
    def last_update_path(self) -> Path:
        return BASE_DIR / "data" / "txt" / self.last_update_file

    @property
    def txt_dir(self) -> Path:
        return BASE_DIR / "data" / "txt"


CONFIG_1D = DownloadConfig(
    interval="1d",
    period_days=365,
    data_folder="d1_parquet_gpw",
    downloaded_tickers_file="first_tier_list.txt",
    tickers_to_download="filtered_T1_list.txt",
    last_update_file="last_update_d1.txt",
    interval_minutes=0,
)

CONFIG_15M = DownloadConfig(
    interval="15m",
    period_days=60,
    data_folder="min15_parquet_gpw",
    downloaded_tickers_file="filtered_T1_list.txt",
    tickers_to_download="filtered_T2_list.txt",
    last_update_file="last_update_min15.txt",
    interval_minutes=15,
)

CONFIG_5M = DownloadConfig(
    interval="5m",
    period_days=1,
    data_folder="min5_parquet_gpw",
    downloaded_tickers_file="filtered_T2_list.txt",
    tickers_to_download="filtered_T3_list.txt",
    last_update_file="last_update_min5.txt",
    interval_minutes=5,
)
