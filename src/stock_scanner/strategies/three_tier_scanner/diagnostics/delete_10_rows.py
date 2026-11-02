import os

import pandas as pd

print("Aktualny katalog roboczy:")
print(os.getcwd())

print("Pliki w folderze:")
for f in os.listdir():
    print(f)

df = pd.read_parquet("11B_WA.parquet")
df = df.iloc[:-1]
df.to_parquet("11B_WA.parquet")
