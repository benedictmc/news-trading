from retrieve_dataset import TradingSimulator
import pandas as pd
import matplotlib.pyplot as plt

symbol = "BTCUSDT"
date = "2023-08"

trading_simulator = TradingSimulator(symbol, date, load_source="blob")
trading_simulator.build_reduced_trades()


df = trading_simulator.reduced_trades_df
df.reset_index(inplace=True)


def plot_price_spikes(df):
    data = df.copy()
    lookforward_period = 10 * 60

    data['rolling_max'] = data['avg_price'].rolling(lookforward_period, min_periods=1).max().shift(-lookforward_period + 1)
    data['rolling_min'] = data['avg_price'].rolling(lookforward_period, min_periods=1).min().shift(-lookforward_period + 1)

    # Identify where the price either falls or rises by 3% within the lookforward window
    data['marker'] = None
    data.loc[data['rolling_max'] >= data['avg_price'] * 1.03, 'marker'] = 'up'
    data.loc[data['rolling_min'] <= data['avg_price'] * 0.97, 'marker'] = 'down'

    # Drop temporary columns
    data.drop(columns=['rolling_max', 'rolling_min'], inplace=True)


    reduced_sample_data = data.sample(2000)

    # Plotting the reduced sample data
    plt.figure(figsize=(15, 8))
    plt.plot(reduced_sample_data['flooored_time'], reduced_sample_data['avg_price'], label='Average Price', color='lightgray')

    # Plot markers for 3% price increase
    plt.scatter(reduced_sample_data[reduced_sample_data['marker'] == 'up']['flooored_time'], 
                reduced_sample_data[reduced_sample_data['marker'] == 'up']['avg_price'], 
                color='g', label='3% Price Increase', marker='^')

    # Plot markers for 3% price decrease
    plt.scatter(reduced_sample_data[reduced_sample_data['marker'] == 'down']['flooored_time'], 
                reduced_sample_data[reduced_sample_data['marker'] == 'down']['avg_price'], 
                color='r', label='3% Price Decrease', marker='v')

    plt.title('Average Price with 3% Price Change Markers (Reduced Sample)')
    plt.xlabel('Time')
    plt.ylabel('Average Price')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    plt.savefig('price_spikes.png')


def plot_ohlc(df):

    df.index = pd.to_datetime(df.index)

    df_resampled = df.resample('1T').agg({
        'avg_price': ['first', 'max', 'min', 'last'],
        'sum_asset_bought': 'sum',
        'sum_asset_sold': 'sum'
    })

    df_resampled.columns = ['_'.join(col).strip() for col in df_resampled.columns.values]
    df_resampled.rename(columns={
        'avg_price_first': 'open',
        'avg_price_max': 'high',
        'avg_price_min': 'low',
        'avg_price_last': 'close'
    }, inplace=True)

    df_resampled.reset_index(inplace=True)


def plot_reduced_trades(df):
    df = df.set_index('flooored_time')

    fig, ax1 = plt.subplots(figsize=(15, 8))

    # Line plot for average price (which is represented by the 'close' column in the resampled data)
    ax1.plot(df.index, df['close'], color='b', label='Average Price', linewidth=2)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Average Price', color='b')
    ax1.tick_params(axis='y', labelcolor='b')

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    width = (df.index[1] - df.index[0]).seconds / (3 * 86400)
    
    # Bar plots for volumes
    ax2.bar(df.index, df['sum_asset_bought_sum'], width=width, alpha=0.6, label='Bought Volume', color='g')
    ax2.bar(df.index, -df['sum_asset_sold_sum'], width=width, alpha=0.6, label='Sold Volume', color='r')
    ax2.set_ylabel('Volume', color='g')  # Green for bought volume
    ax2.tick_params(axis='y', labelcolor='g')

    # Title and show the plot
    plt.title('Trade Dynamics Over Time')
    fig.tight_layout()  # Otherwise the right y-label is slightly clipped
    plt.legend(loc='upper left')
    plt.savefig('trade_dynamics.png')
    plt.show()


def plot_anomalous_time(df):
    df = df[df["flooored_time"] > "2023-08-29 14:19:00"]
    df = df.head(60*2)
    df = df.set_index('flooored_time')

    fig, ax1 = plt.subplots(figsize=(15, 8))


    ax1.plot(df.index, df['avg_price'], color='b', label='Average Price', linewidth=2)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Average Price', color='b')
    # Rotate labels 90 degrees
    plt.xticks(rotation=90)
    fig.tight_layout()  # Otherwise the right y-label is slightly clipped

    plt.savefig('trade.png')
    plt.show()

plot_anomalous_time(df)