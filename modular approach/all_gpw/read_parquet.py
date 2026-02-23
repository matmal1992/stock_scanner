import pandas as pd

df = pd.read_parquet("ticker.parquet")
print(df.head())
print(df.shape)

