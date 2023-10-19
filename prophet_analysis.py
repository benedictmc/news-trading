#import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import scipy.stats as stats
import math
import sklearn
import statsmodels.api as sm
from statsmodels.tsa.api import SimpleExpSmoothing
from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.offline as py
import retrieve_dataset as rd

config = {
    "columns": [
        "avg_price",
        "sum_asset_bought",
        "num_of_trades_bought",
        "sum_asset_sold",
        "num_of_trades_sold",
    ], 
    "features": [
        {
            "type": "zscore",
            "columns":  [
                "sum_asset_bought",
                "num_of_trades_bought",
                "sum_asset_sold",
                "num_of_trades_sold"
            ]
        }
    ], 
    "signal": {
        "column": "sum_asset_sold_zscore",
        "threshold": 100,
    }
}




df = rd.RetriveDataset("BTCUSDT", "2023-09", config).retrieve_trading_dataset()


# df.rename(columns={'flooored_time':'timestamp'}, inplace=True)

# df['SMA'] = df.iloc[:,1].rolling(window=500).mean()
# df['diff'] = df['avg_price'] - df['SMA']
# df[['avg_price','SMA']].plot(figsize=(15,7))