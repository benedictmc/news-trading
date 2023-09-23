import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from retrieve_dataset import RetriveDataset

def plot_data(df, symbol, date=None, plot_folder=None, signal_index=None):

    plt.figure(figsize=(14,7))

    plt.plot(df.index, df['avg_price'], label='avg_price', color='blue')

    # Plot news signals
    signal_data = df[df['news_signal'] == 1]
    if not signal_data.empty:
        plt.scatter(signal_data.index, signal_data['avg_price'], color='orange', marker='o', s=20, label='News Signal')

    plt.xlabel('Time')
    plt.ylabel('Average Price')
    plt.legend()
    plt.title(f'Trade at {signal_index}')
    plt.grid(True)
    if not plot_folder:
        results_folder = f'local/plots/{symbol}/plots/{symbol}'
    else:
        results_folder = f'local/{plot_folder}/{symbol}'
        

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    filepath = f'{results_folder}/data_{signal_index}.png'
    print(f"Saving plot to {filepath}")
    plt.savefig(filepath)
    plt.close()
    
