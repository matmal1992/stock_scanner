from config import CONFIG_15M, CONFIG_1D, CONFIG_5M
from scanners.universal_scanner import run_scan
from report.report_builder import create_empty_report
from strategy_profiles import *
from profiles import PROFILE_T1, PROFILE_T2, PROFILE_T3
from download.downloader import run_download
    
def main():
    report_path = create_empty_report()
    print("===== STAGE 1: DOWNLOAD first tier tickers =====")
    run_download(CONFIG_1D, "<!-- T1_DOWNLOAD -->", "first")

    print("\n===== ETAP 2: ANALIZA first tier tickers =====")
    run_scan(PROFILE_T1)

    print("\n===== STAGE 3: DOWNLOAD second tier tickers =====")
    run_download(CONFIG_15M, "<!-- T2_DOWNLOAD -->", "second")

    print("\n===== ETAP 4: ANALIZA 2nd tier tickers =====")
    run_scan(PROFILE_T2)

    print("\n===== STAGE 5: DOWNLOAD third tier tickers =====")
    run_download(CONFIG_5M, "<!-- T3_DOWNLOAD -->", "third")
    
    print("\n===== ETAP 6: ANALIZA third tier tickers =====")
    run_scan(PROFILE_T3)

    print("\n===== DONE =====")

if __name__ == "__main__":
    main()