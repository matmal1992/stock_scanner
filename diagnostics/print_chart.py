import os

import matplotlib.pyplot as plt
import pandas as pd

parquet_file = "CRI_WA.parquet"

if not os.path.exists(parquet_file):
    print(f"Plik {parquet_file} nie istnieje.")
    exit()

df = pd.read_parquet(parquet_file)

if df.empty:
    print("DataFrame jest pusty.")
    exit()

if "Close" not in df.columns:
    print("Brak kolumny 'Close'.")
    exit()

print("Dane wczytane poprawnie.")
print("Liczba wierszy:", len(df))
print("Zakres dat:", df.index.min(), "->", df.index.max())

if df.index.tz is not None:
    df.index = df.index.tz_localize(None)

plt.figure()
plt.plot(range(len(df)), df["Close"])
plt.title("Creotech Instruments - Close Price")
plt.xlabel("Sesja")
plt.ylabel("Cena zamknięcia")
plt.grid(True)

step = 20
plt.xticks(
    ticks=range(0, len(df), 20),
    labels=df.index.strftime("%Y-%m-%d")[::step],
    rotation=45,
)

ax = plt.gca()


def format_coord(x, y):
    x = int(round(x))
    if 0 <= x < len(df):
        date = df.index[x].strftime("%Y-%m-%d")
        return f"Data: {date} | Cena: {y:.2f}"
    else:
        return ""


ax.format_coord = format_coord

plt.tight_layout()
plt.show()
