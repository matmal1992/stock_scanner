import pandas as pd

df = pd.read_parquet("CRI_WA.parquet")
print(df.head())
print(df.shape)
