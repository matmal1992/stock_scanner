from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
report_path = BASE_DIR / "report.html"

@dataclass
class DownloadConfig:
    interval: str
    period_days: int
    data_folder: str
    tickers_file: str
    last_update_file: str
    
    @property
    def data_dir(self):
        return BASE_DIR / "data" / "parquet" / self.data_folder

    @property
    def tickers_path(self):
        return BASE_DIR / "data" / "txt" / self.tickers_file

    @property
    def last_update_path(self):
        return BASE_DIR / "data" / "txt" / self.last_update_file
    
    @property
    def txt_dir(self):
        return BASE_DIR / "data" / "txt"
    

CONFIG_1D = DownloadConfig(
    interval="1d",
    period_days=365,
    data_folder="d1_parquet_gpw",
    tickers_file="first_tier_list.txt",
    last_update_file="last_update_d1.txt"
)

CONFIG_15M = DownloadConfig(
    interval="15m",
    period_days=50,
    data_folder="min15_parquet_gpw",
    tickers_file="second_tier_list.txt",
    last_update_file="last_update_min15.txt"
)

CONFIG_5M = DownloadConfig(
    interval="5m",
    period_days=1,
    data_folder="min5_parquet_gpw",
    tickers_file="third_tier_list.txt",
    last_update_file="last_update_min5.txt"
)

# later to implement
MIN_TURNOVER = 1_000_000  # PLN

WEIGHTS = {
    "rs": 0.4,
    "volume": 0.2,
    "trend": 0.2,
    "compression": 0.2,
}


