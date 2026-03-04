from dataclasses import dataclass
# from pathlib import Path


# BASE_DIR = Path(__file__).resolve().parent

@dataclass
class DownloadConfig:
    interval: str
    period_days: int
    data_folder: str
    tickers_file: str
    failed_tickers_file: str
    download_report_file: str
    last_update_file: str

CONFIG_1D = DownloadConfig(
    interval="1d",
    period_days=365,
    data_folder="1d_gpw_data_test",
    tickers_file="tickers_xtb_WA_test.txt",
    failed_tickers_file="failed_tickers_1d.txt",
    download_report_file="download_report_1d.txt",
    last_update_file="last_update_1d.txt"
)

CONFIG_15M = DownloadConfig(
    interval="15m",
    period_days=60,
    data_folder="15m_gpw_data",
    tickers_file="tickers_xtb_WA.txt",
    failed_tickers_file="failed_tickers_15m.txt",
    download_report_file="download_report_15m.txt",
    last_update_file="last_update_15m.txt"
)



# later to implement
MIN_TURNOVER = 1_000_000  # PLN

WEIGHTS = {
    "rs": 0.4,
    "volume": 0.2,
    "trend": 0.2,
    "compression": 0.2,
}
