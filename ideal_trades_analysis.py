from retrieve_dataset import RetriveDataset
import pandas as pd

symbol = "APTUSDT"
trading_data = RetriveDataset(symbol, "2023-08")

df = trading_data.retrieve_trading_dataset()

print(df.head())