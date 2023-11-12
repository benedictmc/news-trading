import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()

LOCAL_LOCATION = os.getenv("LOCAL_LOCATION")
if LOCAL_LOCATION == None:
    raise Exception("> plot_data: LOCAL_LOCATION not set. Please make .env file with LOCAL_LOCATION filepath")

COLOURS = [
    'orange',
    'yellow',
    'green',
    'red',
    'purple',
]
MARKERS = [
    'o',
    'v',
    '*',
    '-',
    's',
] 


def plot_data(
    df: pd.DataFrame, 
    symbol: str, 
    add_marker: Optional[pd.DatetimeIndex] = None, 
    marker_title: Optional[str] = None, 
    signals_to_plot: Optional[List[str]] = None, 
    title: Optional[str] = None, 
    plot_folder: Optional[str] = None
):
    plt.figure(figsize=(14,7))

    plt.plot(df.index, df['avg_price'], label='avg_price', color='blue', linewidth=0.75)

    
    # Plot signals if provided
    if signals_to_plot:
        for index, signal_to_plot in enumerate(signals_to_plot):
            colour = COLOURS[index % len(COLOURS)]
            marker = MARKERS[index % len(MARKERS)]
            
            signal_data = df[df[signal_to_plot] == 1]
            if not signal_data.empty:
                plt.scatter(signal_data.index, signal_data['avg_price'], color=colour, marker=marker, s=25, label=signal_to_plot, zorder=2.5)

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
   

    plt.grid(True)

    if not plot_folder:
        results_folder = f'{LOCAL_LOCATION}/plots/{symbol}'
    else:
        results_folder = f'{LOCAL_LOCATION}/{plot_folder}'
        

    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    title_clean = title.replace(" ", "_")
    
    filepath = f'{results_folder}/{title_clean}.png'
    print(f"Saving plot to {filepath}")
    
    plt.savefig(filepath)
    plt.close()
    
