import yfinance as yf
import os
from datetime import datetime, timedelta

INTERVAL = "1d"
DATA_FOLDER = "1d_gpw_data"

tickers_file = "tickers_xtb_WA.txt"

if not os.path.exists(tickers_file):
    print("Brak pliku tickers_xtb_WA.txt")
    exit()

with open(tickers_file, "r") as f:
    tickers = [t.strip() for t in f.read().split(",") if t.strip()]

results = {
    "ok": [],
    "short_history": [],
    "delisted_or_invalid": [],
    "error": []
}

start_date = datetime.today() - timedelta(days=365)

for ticker in tickers:
    print(f"\nSprawdzanie {ticker}...")

    try:
        t = yf.Ticker(ticker)

        # Próba pobrania 1 roku
        df = t.history(start=start_date, interval="1d")

        if not df.empty:
            filename = ticker.replace(".", "_") + ".parquet"
            filepath = os.path.join("1d_gpw_data", filename)
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
