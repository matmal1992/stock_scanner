from download.d1 import d1_down_gpw
from download.d1 import d1_update_gpw
from analysis import first_tier_filter
from download.min15 import min15_down
from download.min15 import min15_update
from analysis import second_tier_filter
import tkinter as tk
from tkinter import messagebox

def confirm_continue(messege):
    root = tk.Tk()
    root.withdraw()  # ukrywa główne okno
    answer = messagebox.askyesno("Potwierdzenie", messege)
    root.destroy()
    return answer
    
def main():
    # confirm_continue("Download first tier data")
    print("===== ETAP 1: DOWNLOAD =====")
    d1_down_gpw.main()

    # # confirm_continue("Update first tier data")
    # print("\n===== ETAP 2: UPDATE =====")
    # # d1_update_gpw.main()
    # # confirm_continue("Analyze first tier data")
    # print("\n===== ETAP 3: ANALIZA =====")
    # # first_tier_filter.main()

    # # confirm_continue("Download second tier data")
    # print("\n===== ETAP 4: DOWNLOAD 15min tickers =====")
    # # min15_down.main()

    # # confirm_continue("Update second tier data")
    # print("\n===== ETAP 5: UPDATE =====")
    # # min15_update.main()

    # # confirm_continue("Analyze second tier data")
    # print("\n===== ETAP 6: ANALIZA =====")
    # # second_tier_filter.main()

    print("\n===== GOTOWE =====")


if __name__ == "__main__":
    main()