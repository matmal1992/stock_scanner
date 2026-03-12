from download import d1_gpw, min15_gpw, min5_gpw
from scanners import tier1_scan, tier2_scan, tier3_scan
from report.report_builder import create_empty_report
    
def main():
    report_path = create_empty_report()
    print("===== STAGE 1: DOWNLOAD first tier tickers =====")
    d1_gpw.main()

    print("\n===== ETAP 2: ANALIZA first tier tickers =====")
    tier1_scan.main()

    print("\n===== STAGE 3: DOWNLOAD second tier tickers =====")
    min15_gpw.main()

    print("\n===== ETAP 4: ANALIZA 2nd tier tickers =====")
    tier2_scan.main()

    print("\n===== STAGE 5: DOWNLOAD third tier tickers =====")
    min5_gpw.main()
    
    print("\n===== ETAP 6: ANALIZA third tier tickers =====")
    tier3_scan.main()

    print("\n===== DONE =====")

if __name__ == "__main__":
    main()