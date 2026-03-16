from download import d1_gpw, min15_gpw, min5_gpw
from scanners.universal_scanner import run_scan
from report.report_builder import create_empty_report
from strategy_profiles import *
from profiles import PROFILE_T1, PROFILE_T2, PROFILE_T3
    
def main():
    report_path = create_empty_report()
    print("===== STAGE 1: DOWNLOAD first tier tickers =====")
    d1_gpw.main()

    print("\n===== ETAP 2: ANALIZA first tier tickers =====")
    run_scan(PROFILE_T1)

    print("\n===== STAGE 3: DOWNLOAD second tier tickers =====")
    min15_gpw.main()

    print("\n===== ETAP 4: ANALIZA 2nd tier tickers =====")
    run_scan(PROFILE_T2)

    print("\n===== STAGE 5: DOWNLOAD third tier tickers =====")
    min5_gpw.main()
    
    print("\n===== ETAP 6: ANALIZA third tier tickers =====")
    run_scan(PROFILE_T3)

    print("\n===== DONE =====")

if __name__ == "__main__":
    main()