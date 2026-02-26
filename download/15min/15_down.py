import yfinance as yf
import os
from datetime import datetime, timedelta
from pathlib import Path

def main():
    INTERVAL = "15min"
    DATA_FOLDER = "15min_gpw_data"

    BASE_DIR = Path(__file__).resolve().parent
    tickers_file = BASE_DIR / "15min_tickers_WA.txt"

    if not tickers_file.exists():
        print("Brak pliku 15min_tickers_WA.txt")
        return

    with open(tickers_file, "r") as f:
        tickers = [t.strip() for t in f.read().split(",") if t.strip()]

    results = {
        "ok": [],
        "short_history": [],
        "delisted_or_invalid": [],
        "error": []
    }

    start_date = datetime.today() - timedelta(days=182)

    for ticker in tickers:
        print(f"\nSprawdzanie {ticker}...")

        try:
            t = yf.Ticker(ticker)

            # próba pobrania danych z pół roku wstecz
            df = t.history(start=start_date, interval="15min")

            if not df.empty:
                filename = ticker.replace(".", "_") + ".parquet"
                filepath = os.path.join(DATA_FOLDER, filename)
                df.to_parquet(filepath)
                results["ok"].append(ticker)
                print("OK - zapisano dane")
                continue

            # Jeśli pusto → sprawdzamy MAX
            df_max = t.history(period="max", interval="1d")

            if df_max.empty:
                results["delisted_or_invalid"].append(ticker)
                print("Brak danych w ogóle - delisted / nieobsługiwany / błędny ticker")
            else:
                results["short_history"].append(ticker)
                print("Spółka notowana krócej niż 1 rok")

        except Exception as e:
            results["error"].append(ticker)
            print("Błąd techniczny:", e)

    print("\n========== RAPORT ==========")
    print("Poprawnie pobrane:", len(results["ok"]))
    print("Krótsza historia:", len(results["short_history"]))
    print("Delisted / niepoprawne:", len(results["delisted_or_invalid"]))
    print("Błędy techniczne:", len(results["error"]))

    # Zapis raportu
    with open("download_report.txt", "w") as f:
        for key, value in results.items():
            f.write(f"{key} ({len(value)}):\n")
            for t in value:
                f.write(f"  {t}\n")
            f.write("\n")
    pass

if __name__ == "__main__":
    main()
