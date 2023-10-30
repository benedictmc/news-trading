import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

LOCAL_LOCATION = os.getenv("LOCAL_LOCATION")
if LOCAL_LOCATION == None:
    raise Exception("> plot_data: LOCAL_LOCATION not set. Please make .env file with LOCAL_LOCATION filepath")

def plot_data(df, symbol, add_marker=None, marker_title=None, signal_to_plot=None, title=None, plot_folder=None, signal_index=None):

    plt.figure(figsize=(14,7))

    plt.plot(df.index, df['avg_price'], label='avg_price', color='blue')


    if signal_to_plot:
        # Plot news signals
        signal_data = df[df[signal_to_plot] == 1]
        if not signal_data.empty:
            plt.scatter(signal_data.index, signal_data['avg_price'], color='orange', marker='o', s=20, label=signal_to_plot)

    # Add marker if provided
    if add_marker:
        if type(add_marker) not in [pd.core.indexes.datetimes.DatetimeIndex, pd._libs.tslibs.timestamps.Timestamp]:
            raise Exception("Error: Marker is not a datetime index")
        
        marker_price = df.loc[add_marker, 'avg_price']

        plt.scatter(add_marker, marker_price, color='red', marker='o', s=40)
        if marker_title:
            plt.annotate(marker_title, (add_marker, marker_price), textcoords="offset points", xytext=(0,10), ha='right')


    plt.xlabel('Time')
    plt.ylabel('Average Price')
    plt.legend()
    if title:
        plt.title(title)
    else:
        plt.title(f'Trade at {signal_index}')

    plt.grid(True)

    if not plot_folder:
        results_folder = f'{LOCAL_LOCATION}/plots/{symbol}/'
    else:
        results_folder = f'{{LOCAL_LOCATION}}/{plot_folder}/{symbol}'
        

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    title_clean = title.replace(" ", "_")
    
    filepath = f'{results_folder}/{title_clean}.png'
    print(f"Saving plot to {filepath}")
    
    plt.savefig(filepath)
    plt.close()
    
