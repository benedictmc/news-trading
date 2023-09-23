import pandas as pd
from prophet import Prophet
from retrieve_dataset import RetriveDataset

symbol = "APTUSDT"

trading_data = RetriveDataset(symbol, "2023-08", 5, 0.01)
df = trading_data.retrieve_trading_dataset()

m = Prophet()
m.fit(df)