from typing import Callable

from src.download.config import CONFIG_1D
from src.download.downloader import run_download


def run_3t_strategy(progress_callback: Callable | None = None) -> None:
    print("===== STAGE 1: DOWNLOAD first tier tickers =====")
    run_download(CONFIG_1D, "<!-- T1_DOWNLOAD -->", "first", progress_callback)

    # print("\n===== ETAP 2: ANALIZA first tier tickers =====")
    # run_scan(PROFILE_T1)

    # print("\n===== STAGE 3: DOWNLOAD second tier tickers =====")
    # run_download(CONFIG_15M, "<!-- T2_DOWNLOAD -->", "second")

    # print("\n===== ETAP 4: ANALIZA 2nd tier tickers =====")
    # run_scan(PROFILE_T2)

    # print("\n===== STAGE 5: DOWNLOAD third tier tickers =====")
    # run_download(CONFIG_5M, "<!-- T3_DOWNLOAD -->", "third")

    # print("\n===== ETAP 6: ANALIZA third tier tickers =====")
    # run_scan(PROFILE_T3)

    print("\n===== DONE =====")
