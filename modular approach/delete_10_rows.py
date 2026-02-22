import pandas as pd
import os

print("Aktualny katalog roboczy:")
print(os.getcwd())

print("Pliki w folderze:")
for f in os.listdir():
    print(f)

df = pd.read_parquet("CRI_PL.parquet")
df = df.iloc[:-10]
df.to_parquet("CRI_PL.parquet", index=False)
