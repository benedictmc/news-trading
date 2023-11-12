from retrieve_binance.retrieve_dataset import RetriveDataset
from retrieve_binance.plot_data import plot_data
import pandas as pd
import copy
import os
import time
from dotenv import load_dotenv
import json
import numpy as np
import matplotlib.pyplot as plt

load_dotenv()

LOCAL_LOCATION = os.getenv("LOCAL_LOCATION")


# Signal function to pass in to the config
def add_signal(df):
    df['signal'] = 0


    df['news_signal_past_45'] = df['news_signal'].rolling(window=10).max()

    mask = (
        ((df['sum_asset_sold_zscore'] > 220) | (df['num_of_trades_sold_zscore'] > 220)) & 
        (df['news_signal_past_45'] == 1)
    )

    df.loc[mask, 'signal'] = 1

    # for index, _ in df[df['news_signal'] == 1].iterrows():
    #     i_index = df.index.get_loc(index)
    #     start_price = df.iloc[i_index]['avg_price']
    #     end_idx = min(i_index + 60*60, len(df)) 
    #     max_change = 0

    #     for i in range(i_index+1, end_idx):
    #         val = df.iloc[i]['avg_price']
    #         pct_change = round(abs((val - start_price) / start_price), 4)

    #         max_change = max(max_change, pct_change)

    #     df.loc[index, 'signal'] = max_change
    # mask = df['news_signal'] == 1
    
    # # Calculate rolling max and min over the next 60*60 values
    # rolling_max = df['avg_price'].shift(-1).rolling(window=60*60, min_periods=1).max()
    # rolling_min = df['avg_price'].shift(-1).rolling(window=60*60, min_periods=1).min()

    # # Calculate the percentage changes
    # pct_change_max = ((rolling_max - df['avg_price']) / df['avg_price']).abs()
    # pct_change_min = ((df['avg_price'] - rolling_min) / df['avg_price']).abs()

    # # Calculate the maximum of the two percentage changes and assign to the signal column
    # df.loc[mask, 'signal'] = pct_change_max.combine(pct_change_min, max)

    return df



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
            "type": "news_signal"
        }, 
        {
            "type": "future_diff",
            "columns": [
                "avg_price"
            ],
            "periods": [
              60,
            ]
        }, 
    ]
}

feature_config = {
    "columns": [
        "avg_price",
        "sum_asset_bought",
        "num_of_trades_bought",
        "sum_asset_sold",
        "num_of_trades_sold",
    ], 
    "features": [
        {
            "type": "news_signal"
        }, 
        {
            "type": "future_diff",
            "columns": [
                "avg_price"
            ],
            "periods": [
              60,
            ]
        }, 
        {
            "type": "zscore",
            "columns": [
                "sum_asset_bought",
                "num_of_trades_bought",
                "sum_asset_sold",
                "num_of_trades_sold",
            ]
        },
        {
            "type": "moving_average",
            "periods": [
              5,
            ],
            "columns": [
                "sum_asset_bought_zscore",
                "num_of_trades_bought_zscore",
                "sum_asset_sold_zscore",
                "num_of_trades_sold_zscore",
            ]
        }, 
        {
            "type": "ratio",
            "columns": [
                "sum_asset_bought_zscore_moving_average_MA_5",
                "sum_asset_sold_zscore_moving_average_MA_5",
            ],
            "column_name": "sum_asset_bought_to_sold_ratio"
        }, 
        {
            "type": "ratio",
            "columns": [
                "num_of_trades_bought_zscore_moving_average_MA_5",
                "num_of_trades_sold_zscore_moving_average_MA_5",
            ],
            "column_name": "num_of_trades_bought_to_sold_ratio"
        }
    ], 
    "signal_function": add_signal
}


def visualise_signal(df, signal_index, symbol, date, should_plot=False, should_save_csv=False):
    signal_df = df.loc[signal_index:signal_index+pd.Timedelta(minutes=30)]

    timestamp = (signal_index - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

    print("=====================================")
    print(f"> {symbol} Signal at {signal_index}")
    print(f"> Timestamp: {timestamp}")
    print("=====================================")

    if should_plot:
        plot_df = df.loc[signal_index-pd.Timedelta(minutes=5):signal_index+pd.Timedelta(minutes=60)]
        plot_data(plot_df, symbol, signal_to_plot="news_signal", plot_folder=f"top_news/{symbol}", title=f"{symbol} {date} {signal_index}")

    if should_save_csv:
        save_df = df.loc[signal_index-pd.Timedelta(minutes=1):signal_index+pd.Timedelta(minutes=60)]
        plot_data(save_df, symbol, add_marker=signal_index, signal_to_plot="signal", plot_folder=f"signals/{symbol}", title=f"{symbol} {date} {signal_index}")
        save_df.to_csv(f'{LOCAL_LOCATION}/signals/{symbol}/{symbol}_{date}_{timestamp}.csv')
        

def backtest(df):

    df["ema_buy"] = df.num_of_trades_bought.ewm(alpha=0.75, adjust=False).mean()
    df["ema_sell"] = df.num_of_trades_sold.ewm(alpha=0.75, adjust=False).mean()

    trade = False
    trade_index = None
    buy_trades = 0
    sell_trades = 0
    time_max, current_time = 60*2, 0 
    # Iterates over time after the signal
    for i, row in df.iterrows():
        if row.signal == 1 and not trade:
            trade = True
            start_price = row.avg_price
            trade_index = i
            print(f"Trade Started: {i}")
            continue
    
        if trade:
            print("****")
            print(f"Trade: {row.floored_time}. Price {row.avg_price}")
            price_diff = round((row.avg_price - start_price) / start_price, 4)
            print(f"Price Diff: {price_diff}")
            print(f"Sum Ratio: {row.sum_asset_bought_to_sold_ratio} Num Ratio: {row.num_of_trades_bought_to_sold_ratio}")
            buy_sell_delta = row.ema_sell - row.ema_buy
            print(f"The buy trades ema: {row.ema_buy} and sell trades ema: {row.ema_sell}, buy sell delta: {buy_sell_delta}")
            buy_trades += row.num_of_trades_bought 
            sell_trades += row.num_of_trades_sold
            print(f"Buy Trades: {buy_trades}, Sell Trades: {sell_trades}")

            # if buy_trades > sell_trades:
            #     print(f"Ending Trade: {i}")
            #     return
            current_time += 1
            if current_time > 5 and buy_sell_delta < 0:
                print(f"Ending Trade: {i}")
                return

            
            if current_time > time_max:
                return
            
            time.sleep(.1)
        # price_diff = round((row.avg_price - start_price) / start_price, 4)
        # sum_bought_zscore = round(row.sum_asset_bought_zscore, 2)
        # sum_sold_zscore = round(row.sum_asset_sold_zscore, 2)
        # num_bought_zscore = round(row.num_of_trades_bought_zscore, 2)
        # num_sold_zscore = round(row.num_of_trades_sold_zscore, 2)

        # row.sum_asset_bought_zscore_moving_average_MA_5
        # row.num_of_trades_bought_zscore_moving_average_MA_5
        # row.sum_asset_sold_zscore_moving_average_MA_5
        # row.num_of_trades_sold_zscore_moving_average_MA_5

        # total_zscore = round(abs(row.sum_asset_bought_zscore) + abs(row.num_of_trades_bought_zscore) + abs(row.sum_asset_sold_zscore) + abs(row.num_of_trades_sold_zscore), 2)




#         if should_plot:
#             # plot_df = df.loc[i:signal_index+pd.Timedelta(minutes=60)]
#             marker_title = f"""
# Current Time: {i} 
# Price Diff: {price_diff} 
# ======ZScore=======
# Asset Bought Zscore: {sum_bought_zscore} 
# Asset Sold Zscore: {sum_sold_zscore} 
# Num Bought Zscore: {num_bought_zscore} 
# Num Sold Zscore: {num_sold_zscore} 
# ======5 MA ZScore=======
# Asset Bought Trades 5 MA Zscore: {row.sum_asset_bought_zscore_moving_average_MA_5} 
# Asset Sold Trades 5 MA Zscore: {row.sum_asset_sold_zscore_moving_average_MA_5} 
# Num Bought Trades 5 MA Zscore: {row.num_of_trades_bought_zscore_moving_average_MA_5} 
# Num Sold Trades 5 MA Zscore: {row.num_of_trades_sold_zscore_moving_average_MA_5} 
# ======Ratio=======
# Num Bought to Sold Ratio: {row.num_of_trades_bought_to_sold_ratio}
# Sum Bought to Sold Ratio: {row.sum_asset_bought_to_sold_ratio}
#             """
#             print(marker_title)
#             plot_data(plot_df, symbol, add_marker=i, marker_title=marker_title, title=f"TRADE")

#         time.sleep(2)

# symbols = ["ACHUSDT", "ALPHAUSDT", "ZILUSDT"]
# indexes = [pd.to_datetime("2023-09-21 08:48:10"), pd.to_datetime("2023-09-19 07:03:07"), pd.to_datetime("2023-09-13 03:00:09")]
# Good Signal
# symbol = "ACHUSDT"
# signal_index = pd.to_datetime("2023-09-21 08:48:10")

# # Bad Signal
# symbol = "ALPHAUSDT"
# signal_index = pd.to_datetime("2023-09-19 07:03:07")


# # Quick exit signal
# symbol = "ZILUSDT"
# signal_index = pd.to_datetime("2023-09-13 03:00:09")


# symbol = "CRVUSDT"


# with open("notable_news.json") as f:
#     notable_news = json.load(f)

# print(len(notable_news))

# for news_item in notable_news:
#     symbol = news_item["symbol"]

#     df = RetriveDataset(symbol=symbol, date=date, config=copy.deepcopy(feature_config)).retrieve_trading_dataset()
#     signal_index = pd.to_datetime(news_item["date"])
#     backtest(df, signal_index, symbol, date, should_save_csv=True)

    # try:
    #     df = RetriveDataset(symbol=symbol, date=date, config=copy.deepcopy(feature_config)).retrieve_trading_dataset()
        
    #     if not os.path.exists(f'{LOCAL_LOCATION}/top_movements/{symbol}/{date}'):
    #         os.makedirs(f'{LOCAL_LOCATION}/top_movements/{symbol}/{date}')

    #     filtered_df = df.loc[df['news_signal'] == 1].sort_values(by='signal', ascending=True)
    #     filtered_df.to_csv(f'{LOCAL_LOCATION}/top_movements/{symbol}/{date}/{date}_news_signal.csv')
    # except:
    #     pass




date = "2023-09"

def plot_decay(index, buy_trades, sell_trades, symbol):
    
    def exponential_moving_average(data, alpha=0.5):
        return pd.Series(data).ewm(alpha=alpha, adjust=False).mean().tolist()

    # Calculate EMA
    ema_buy = exponential_moving_average(buy_trades)
    ema_sell = exponential_moving_average(sell_trades)

    # Compute the delta (difference in EMA)
    delta_buy = np.diff(ema_buy, prepend=ema_buy[0])
    delta_sell = np.diff(ema_sell, prepend=ema_sell[0])

    # Apply exponential decay to the deltas
    alpha_decay = 0.5  # adjust based on your needs
    decayed_delta_buy = np.zeros_like(delta_buy)
    decayed_delta_sell = np.zeros_like(delta_sell)

    decayed_delta_buy[0] = delta_buy[0]
    decayed_delta_sell[0] = delta_sell[0]

    for i in range(1, len(delta_buy)):
        decayed_delta_buy[i] = delta_buy[i] + (1 - alpha_decay) * decayed_delta_buy[i-1]
        decayed_delta_sell[i] = delta_sell[i] + (1 - alpha_decay) * decayed_delta_sell[i-1]


    index = index[55:100]
    ema_buy = ema_buy[55:100]
    ema_sell = ema_sell[55:100]
    # Plot
    plt.figure(figsize=(12, 6))
    plt.plot(index, ema_buy, marker='o', label='Buy Trades Decayed Delta')
    plt.plot(index, ema_sell, marker='x', label='Sell Trades Decayed Delta')
    plt.title("Decayed Delta of Buy and Sell Trades using EMA")
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    plt.savefig(f"{symbol}_decay.png")


def find_signals():
    with open('symbols.json') as f:
        symbols = json.load(f)

    signal_key = 'sum_asset_sold_zscore > 120 OR num_of_trades_sold_zscore > 120'

    for symbol in symbols:
        try:
            df = RetriveDataset(symbol=symbol, date=date, config=copy.deepcopy(feature_config)).retrieve_trading_dataset()
            symbol_df = df[df['signal'] == 1]

            for index, row in symbol_df.iterrows():
                backtest(df, index, symbol, date, should_save_csv=True)

            
            if len(symbol_df) == 0:
                continue

            if not os.path.exists(f'{LOCAL_LOCATION}/signals/{symbol}'):
                os.makedirs(f'{LOCAL_LOCATION}/signals/{symbol}')

            print("Saving signal df")
            print(f"Saving to {LOCAL_LOCATION}/signals/{symbol}/symbol_df.csv")
            symbol_df.to_csv(f'{LOCAL_LOCATION}/signals/{symbol}/symbol_df.csv')
        except:
            pass


# find_signals()


def find_exit():
    max_, i = 20, 0 


    for symbol in os.listdir(f'{LOCAL_LOCATION}/signals/'):
        print(symbol)
        for file_ in os.listdir(f'{LOCAL_LOCATION}/signals/{symbol}/'):
            if symbol in file_ and ".csv" in file_:
                print(file_)
                # file_ = "LEVERUSDT_2023-09_1695731425.csv"
                # symbol = "LEVERUSDT"
                df = pd.read_csv(f'{LOCAL_LOCATION}/signals/{symbol}/{file_}')

                df['floored_time'] = pd.to_datetime(df['floored_time'])
                plot_decay(df['floored_time'], df['num_of_trades_bought'], df['num_of_trades_sold'], symbol)
                backtest(df)
                

                # backtest(df)
                # exit()
                # i +=1
                # if i > max_:
                    

                # for index, row in df.iterrows():


find_exit()