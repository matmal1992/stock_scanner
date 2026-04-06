from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
report_path = BASE_DIR / "report.html"


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
