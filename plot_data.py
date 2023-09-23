import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from retrieve_dataset import RetriveDataset

def plot_all_data(df, symbol, date):

    plt.figure(figsize=(14,7))

    plt.plot(df.index, df['avg_price'], label='avg_price', color='blue')

    # Plot news signals
    signal_data = df[df['news_signal'] == 1]
    if not signal_data.empty:
        plt.scatter(signal_data.index, signal_data['avg_price'], color='orange', marker='o', s=20, label='News Signal')

    plt.xlabel('Time')
    plt.ylabel('Average Price')
    plt.legend()
    plt.grid(True)
    results_folder = f'local/plots/{symbol}/plots/{symbol}'

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    filepath = f'{results_folder}/all_data_{date}.png'
    print(f"Saving plot to {filepath}")
    plt.savefig(filepath)

symbol = "ETHUSDT"

x = RetriveDataset(symbol, "2023-08", 5, 0.01)
trading_df = x.retrieve_trading_dataset()

trading_df['index'] = pd.to_datetime(trading_df['index'], format='%Y-%m-%d %H:%M:%S')

# Replace NaN or Inf with 0
trading_df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)

trading_df.set_index('index', inplace=True)

#Filter df between 2023-08-09 12:30:05 and 2023-08-09 13:30:05
# trading_df = trading_df.loc['2023-08-09 12:27:00':'2023-08-09 12:35:00']

print(trading_df.signal.value_counts())

# plot_all_data(trading_df, symbol, "2023-08")

# trading_df.to_csv(f'local/plots/{symbol}/{symbol}.csv')