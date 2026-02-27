import pandas as pd
import numpy as np
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

DATA_DIR = Path("1d/1d_gpw_data")

def confirm_continue(count):
    root = tk.Tk()
    root.withdraw()  # ukrywa główne okno

    answer = messagebox.askyesno(
        "Potwierdzenie",
        f"Znaleziono {count} spółek.\nCzy chcesz kontynuować?"
    )

    root.destroy()
    return answer

def r2(series):
    y = series.values
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    y_pred = slope * x + intercept

    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    return 1 - ss_res / ss_tot if ss_tot != 0 else 0


def calculate_metrics(df):

    if len(df) < 60:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # --- 20D return ---
    ret_20d = close.iloc[-1] / close.iloc[-20] - 1

    # --- R2 trend (60D) ---
    trend_r2 = r2(close.tail(60))

    # --- ATR(14) ---
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr14 = tr.rolling(14).mean().iloc[-1]
    atr_pct = atr14 / close.iloc[-1]

    # --- avg turnover ---
    avg_turnover = (close * volume).rolling(20).mean().iloc[-1]

    # --- compression ---
    range_20 = (high - low).rolling(20).mean().iloc[-1]
    range_5 = (high - low).rolling(5).mean().iloc[-1]
    compression_ratio = range_5 / range_20 if range_20 != 0 else 1

    return {
        "ret_20d": ret_20d,
        "trend_r2": trend_r2,
        "atr_pct": atr_pct,
        "avg_turnover": avg_turnover,
        "compression_ratio": compression_ratio,
    }


def scan_directory():

    candidates = []

    for path in DATA_DIR.glob("*.parquet"):

        ticker = path.stem  # nazwa pliku bez .parquet

        try:
            df = pd.read_parquet(path)
            metrics = calculate_metrics(df)

            if metrics is None:
                continue

            # --- FILTR ---
            if (
                metrics["ret_20d"] > 0.05
                and metrics["trend_r2"] > 0.5
                and metrics["atr_pct"] > 0.02
                and metrics["avg_turnover"] > 1_000_000
                and metrics["compression_ratio"] < 0.7
            ):
                candidates.append((ticker, metrics))

        except Exception as e:
            print(f"Błąd przy {ticker}: {e}")

    return candidates

def main():
    results = scan_directory()

    print("\n=== SPEŁNIAJĄCE WARUNKI ===")
    print("-" * 50)

    for ticker, m in results:
        print(
            f"{ticker} | "
            f"20D: {m['ret_20d']:.2%} | "
            f"R²: {m['trend_r2']:.2f} | "
            f"ATR%: {m['atr_pct']:.2%} | "
            f"Turnover: {m['avg_turnover']:,.0f} | "
            f"Comp: {m['compression_ratio']:.2f}"
        )

    print("-" * 50)
    print(f"Znaleziono: {len(results)} spółek")

    tickers_only = [ticker for ticker, _ in results]

    print("\n=== LISTA SPÓŁEK ===")
    for t in tickers_only:
        print(t)

    if not results:
        print("Brak kandydatów.")
        return

    if confirm_continue(len(results)):
        print("Kontynuuję działanie...")
        # tutaj dalsza logika
    else:
        print("Przerwano przez użytkownika.")
        return
    
if __name__ == "__main__":
    main()


