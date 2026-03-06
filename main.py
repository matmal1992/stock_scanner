from download import d1_gpw, min15_gpw, min5_gpw
from analysis import first_tier_filter
# from analysis import second_tier_filter
# import tkinter as tk
# from tkinter import messagebox
# import os
from report.report_builder import create_empty_report

# def confirm_continue(messege):
#     root = tk.Tk()
#     root.withdraw()  # ukrywa główne okno
#     answer = messagebox.askyesno("Potwierdzenie", messege)
#     root.destroy()
#     return answer
    
def main():
    report_path = create_empty_report()
    print("===== STAGE 1: DOWNLOAD first tier tickers =====")
    d1_gpw.main()

    print("\n===== ETAP 2: ANALIZA first tier tickers =====")
    first_tier_filter.main()

    print("\n===== STAGE 3: DOWNLOAD second tier tickers =====")
    min15_gpw.main()

    # print("\n===== ETAP 6: ANALIZA =====")
    # # second_tier_filter.main()

    print("\n===== STAGE 5: DOWNLOAD third tier tickers =====")
    min5_gpw.main()

    print("\n===== DONE =====")
    # os.startfile(report_path)

if __name__ == "__main__":
    main()