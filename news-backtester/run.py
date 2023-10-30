from retrieve_binance.retrieve_dataset import RetriveDataset
from retrieve_binance.plot_data import plot_data
import pandas as pd
import copy
import os
import time


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
        }
    ]
}

symbols = [
    "BTCUSDT",
    "ETHUSDT",
    "BCHUSDT",
    "XRPUSDT",
    "EOSUSDT",
    "LTCUSDT",
    "TRXUSDT",
    "ETCUSDT",
    "LINKUSDT",
    "XLMUSDT",
    "ADAUSDT",
    "XMRUSDT",
    "DASHUSDT",
    "ZECUSDT",
    "XTZUSDT",
    "BNBUSDT",
    "ATOMUSDT",
    "ONTUSDT",
    "IOTAUSDT",
    "BATUSDT",
    "VETUSDT",
    "NEOUSDT",
    "QTUMUSDT",
    "IOSTUSDT",
    "THETAUSDT",
    "ALGOUSDT",
    "ZILUSDT",
    "KNCUSDT",
    "ZRXUSDT",
    "COMPUSDT",
    "OMGUSDT",
    "DOGEUSDT",
    "SXPUSDT",
    "KAVAUSDT",
    "BANDUSDT",
    "RLCUSDT",
    "WAVESUSDT",
    "MKRUSDT",
    "SNXUSDT",
    "DOTUSDT",
    "DEFIUSDT",
    "YFIUSDT",
    "BALUSDT",
    "CRVUSDT",
    # "TRBUSDT",
    "RUNEUSDT",
    "SUSHIUSDT",
    "SRMUSDT",
    "EGLDUSDT",
    "SOLUSDT",
    "ICXUSDT",
    "STORJUSDT",
    "BLZUSDT",
    "UNIUSDT",
    "AVAXUSDT",
    "FTMUSDT",
    "HNTUSDT",
    "ENJUSDT",
    "FLMUSDT",
    "TOMOUSDT",
    "RENUSDT",
    "KSMUSDT",
    "NEARUSDT",
    "AAVEUSDT",
    "FILUSDT",
    "RSRUSDT",
    "LRCUSDT",
    "MATICUSDT",
    "OCEANUSDT",
    "CVCUSDT",
    "BELUSDT",
    "CTKUSDT",
    "AXSUSDT",
    "ALPHAUSDT",
    "ZENUSDT",
    "SKLUSDT",
    "GRTUSDT",
    "1INCHUSDT",
    "CHZUSDT",
    "SANDUSDT",
    "ANKRUSDT",
    "BTSUSDT",
    "LITUSDT",
    "UNFIUSDT",
    "REEFUSDT",
    "RVNUSDT",
    "SFPUSDT",
    "XEMUSDT",
    "BTCSTUSDT",
    "COTIUSDT",
    "CHRUSDT",
    "MANAUSDT",
    "ALICEUSDT",
    "HBARUSDT",
    "ONEUSDT",
    "LINAUSDT",
    "STMXUSDT",
    "DENTUSDT",
    "CELRUSDT",
    "HOTUSDT",
    "MTLUSDT",
    "OGNUSDT",
    "NKNUSDT",
    "SCUSDT",
    "DGBUSDT",
    "1000SHIBUSDT",
    "BAKEUSDT",
    "GTCUSDT",
    "BTCDOMUSDT",
    "IOTXUSDT",
    "AUDIOUSDT",
    "RAYUSDT",
    "C98USDT",
    "MASKUSDT",
    "ATAUSDT",
    "DYDXUSDT",
    "1000XECUSDT",
    "GALAUSDT",
    "CELOUSDT",
    "ARUSDT",
    "KLAYUSDT",
    "ARPAUSDT",
    "CTSIUSDT",
    "LPTUSDT",
    "ENSUSDT",
    "PEOPLEUSDT",
    "ANTUSDT",
    "ROSEUSDT",
    "DUSKUSDT",
    "FLOWUSDT",
    "IMXUSDT",
    "API3USDT",
    "GMTUSDT",
    "APEUSDT",
    "WOOUSDT",
    "FTTUSDT",
    "JASMYUSDT",
    "DARUSDT",
    "GALUSDT",
    "OPUSDT",
    "INJUSDT",
    "STGUSDT",
    "SPELLUSDT",
    "1000LUNCUSDT",
    "LUNA2USDT",
    "LDOUSDT",
    "CVXUSDT",
    "ICPUSDT",
    "APTUSDT",
    "QNTUSDT",
    "BLUEBIRDUSDT",
    "FETUSDT",
    "FXSUSDT",
    "HOOKUSDT",
    "MAGICUSDT",
    "TUSDT",
    "RNDRUSDT",
    "HIGHUSDT",
    "MINAUSDT",
    "ASTRUSDT",
    "AGIXUSDT",
    "PHBUSDT",
    "GMXUSDT",
    "CFXUSDT",
    "STXUSDT",
    "COCOSUSDT",
    "BNXUSDT",
    "ACHUSDT",
    "SSVUSDT",
    "CKBUSDT",
    "PERPUSDT",
    "TRUUSDT",
    "LQTYUSDT",
    "USDCUSDT",
    "IDUSDT",
    "ARBUSDT",
    "JOEUSDT",
    "TLMUSDT",
    "AMBUSDT",
    "LEVERUSDT",
    "RDNTUSDT",
    "HFTUSDT",
    "XVSUSDT",
    "BLURUSDT",
    "EDUUSDT",
    "IDEXUSDT",
    "SUIUSDT",
    "1000PEPEUSDT",
    "1000FLOKIUSDT",
    "UMAUSDT",
    "RADUSDT",
    "KEYUSDT",
    "COMBOUSDT",
    "NMRUSDT",
    "MDTUSDT",
    "XVGUSDT",
    "WLDUSDT",
    "PENDLEUSDT",
    "ARKMUSDT",
    "AGLDUSDT",
    "YGGUSDT",
    "DODOXUSDT"
]

existing_files = os.listdir('local/top_news')

def backtest(df, signal_index, symbol, date, should_plot=False):
    signal_df = df.loc[signal_index:signal_index+pd.Timedelta(minutes=30)]

    timestamp = (signal_index - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

    print("=====================================")
    print(f"> {symbol} Signal at {signal_index}")
    print(f"> Timestamp: {timestamp}")
    print("=====================================")

    if should_plot:
        plot_df = df.loc[signal_index-pd.Timedelta(minutes=5):signal_index+pd.Timedelta(minutes=60)]
        plot_data(plot_df, symbol, signal_to_plot="news_signal", title=f"{symbol} {date} {signal_index}")

    start_price = signal_df.iloc[0].avg_price

    # Iterates over time after the signal
    for i, row in signal_df.iterrows():
        price_diff = round((row.avg_price - start_price) / start_price, 4)
        sum_bought_zscore = round(row.sum_asset_bought_zscore, 2)
        sum_sold_zscore = round(row.sum_asset_sold_zscore, 2)
        num_bought_zscore = round(row.num_of_trades_bought_zscore, 2)
        num_sold_zscore = round(row.num_of_trades_sold_zscore, 2)


        print(i, row.avg_price, price_diff)
        print(f"> sum_asset_bought_zscore: {sum_bought_zscore}")
        print(f"> num_of_trades_bought_zscore: {num_bought_zscore}")
        print(f"> sum_asset_sold_zscore: {sum_sold_zscore}")
        print(f"> num_of_trades_sold_zscore: {num_sold_zscore}")

        total_zscore = round(abs(row.sum_asset_bought_zscore) + abs(row.num_of_trades_bought_zscore) + abs(row.sum_asset_sold_zscore) + abs(row.num_of_trades_sold_zscore), 2)
        print(f"> ============= total_zscore: {total_zscore}")
        if should_plot:
            # plot_df = df.loc[i:signal_index+pd.Timedelta(minutes=60)]
            marker_title = f"Current Time: {i} \n Price Diff: {price_diff} \n Asset Bought Zscore: {sum_bought_zscore} \n Asset Sold Zscore: {sum_sold_zscore}"
            plot_data(plot_df, symbol, add_marker=i, marker_title=marker_title, title=f"TRADE")

        time.sleep(2)


date = "2023-09"

# Good Signal
symbol = "ACHUSDT"
signal_index = pd.to_datetime("2023-09-21 08:48:10")

# Bad Signal
symbol = "ALPHAUSDT"
signal_index = pd.to_datetime("2023-09-19 07:03:07")


# Quick exit signal
symbol = "ZILUSDT"
signal_index = pd.to_datetime("2023-09-13 03:00:09")


df = RetriveDataset(symbol=symbol, date=date, config=copy.deepcopy(feature_config)).retrieve_trading_dataset()
signal_df = df.loc[signal_index-pd.Timedelta(minutes=2):signal_index+pd.Timedelta(minutes=5)]
signal_df.to_csv(f'test_{symbol}_{date}.csv')

# backtest(df, signal_index, symbol, date, should_plot=True)



# Find and creates and signals
# for symbol in symbols:

#     try:
        # retrieve_dataset = RetriveDataset(symbol=symbol, date=date, config=copy.deepcopy(feature_config)).retrieve_trading_dataset()


        # top_change_df = price_change_df[price_change_df['abs_avg_price_future_diff_60'] > 0.01]

        # has_one_percent = len(top_change_df) > 0

        # if has_one_percent:
        #     pass
#         if f'{symbol}_{date}.csv' in existing_files:

#             backtest(f'local/top_news/{symbol}_{date}.csv')

#         continue
#         print("=====================================")
#         print(f"Processing {symbol}")
#         print("=====================================")
#         retrieve_dataset = RetriveDataset(symbol=symbol, date=date, config=copy.deepcopy(feature_config))

#         df = retrieve_dataset.retrieve_trading_dataset()
        

#         signal_data = df[df["news_signal"] == 1].copy()
#         signal_data['timestamp'] = (signal_data.index - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')

#         # Create a temporary column with absolute values
#         signal_data['abs_avg_price_future_diff_60'] = signal_data['avg_price_future_diff_60'].abs()

#         # Sort by the temporary column
#         sorted_signal_data = signal_data.sort_values(by='abs_avg_price_future_diff_60', ascending=False)

#         # Drop the temporary column if not needed
#         signal_data.drop('abs_avg_price_future_diff_60', axis=1, inplace=True)
#         top_news = sorted_signal_data.head(10)
#         print(top_news)
#         top_news.to_csv(f'local/top_news/{symbol}_{date}.csv')
#     except:
#         print(f"Error processing {symbol}")





