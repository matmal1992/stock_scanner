from download.d1 import d1_down_gpw
from download.d1 import d1_update_gpw
from analysis import first_tier_filter
from download.min15 import min15_down
from download.min15 import min15_update
from analysis import second_tier_filter


def main():
    print("===== ETAP 1: DOWNLOAD =====")
    # d1_down_gpw.main()

    print("\n===== ETAP 2: UPDATE =====")
    # d1_update_gpw.main()

    print("\n===== ETAP 3: ANALIZA =====")
    first_tier_filter.main()

    print("\n===== ETAP 4: DOWNLOAD 15min tickers =====")
    min15_down.main()

    print("\n===== ETAP 5: UPDATE =====")
    min15_update.main()

    print("\n===== ETAP 6: ANALIZA =====")
    second_tier_filter.main()

    print("\n===== GOTOWE =====")


if __name__ == "__main__":
    main()