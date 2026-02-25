from download import d1_down_gpw
from download import d1_update_gpw
from analysis import print_tickers_for_15m


def main():
    print("===== ETAP 1: DOWNLOAD =====")
    d1_down_gpw.main()

    print("\n===== ETAP 2: UPDATE =====")
    d1_update_gpw.main()

    print("\n===== ETAP 3: ANALIZA =====")
    print_tickers_for_15m.main()

    print("\n===== GOTOWE =====")


if __name__ == "__main__":
    main()