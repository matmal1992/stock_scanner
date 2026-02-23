import yfinance as yf

ticker = "CRI.WA" 

df = yf.Ticker(ticker).history(period="1y", interval="1d")

# Save to CSV
df.to_parquet("CRI_WA.parquet")

print("Data saved successfully!")
