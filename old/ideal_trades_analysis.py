from retrieve_dataset import RetriveDataset
import pandas as pd
import numpy as np
from plot_data import plot_data

def add_signal_column(df, signal_type):

    if signal_type == "ideal_trade":
        df['avg_price_5s'] = df['avg_price'].shift(-5)
        df['avg_price_20s'] = df['avg_price'].shift(-20)
        df['avg_price_60s'] = df['avg_price'].shift(-60)
        df['avg_price_15m'] = df['avg_price'].shift(-900)  # 15 minutes = 900 seconds
        df['avg_price_30m'] = df['avg_price'].shift(-1800)  # 30 minutes = 1800 seconds
        df['avg_price_60m'] = df['avg_price'].shift(-3600)  # 60 minutes = 3600 seconds

        # Now, calculate the percentage change for each interval
        df['pct_change_5s'] = (df['avg_price_5s'] - df['avg_price']) / df['avg_price']
        df['pct_change_20s'] = (df['avg_price_20s'] - df['avg_price']) / df['avg_price']
        df['pct_change_60s'] = (df['avg_price_60s'] - df['avg_price']) / df['avg_price']
        df['pct_change_15m'] = (df['avg_price_15m'] - df['avg_price']) / df['avg_price']
        df['pct_change_30m'] = (df['avg_price_30m'] - df['avg_price']) / df['avg_price']
        df['pct_change_60m'] = (df['avg_price_60m'] - df['avg_price']) / df['avg_price']

        df['isIdealTrade'] = np.where(
            (df['pct_change_5s'] > 0.005) &
            (df['pct_change_20s'] > 0.0075) &
            (df['pct_change_60s'] > 0.01) &
            (df['pct_change_15m'] > 0.02) &
            (df['pct_change_30m'] > 0.075) &
            (df['pct_change_60m'] > 0.10),
            1, 0
        )    
    if signal_type == "high_zscore":

        df['high_zscore'] = np.where(
            (df['num_of_trades_sold_zscore'] > 100),
            1, 0
        )

    return df


def get_ideal_trade_surronding_data(df, signal_index):
    # drop_cols = [
    #     "isIdealTrade",
    #     "avg_price_5s",
    #     "avg_price_20s",
    #     "avg_price_60s",
    #     "avg_price_15m",
    #     "avg_price_30m",
    #     "avg_price_60m",
    #     "pct_change_5s",
    #     "pct_change_20s",
    #     "pct_change_60s",
    #     "pct_change_15m",
    #     "pct_change_30m",
    #     "pct_change_60m"
    # ]

    # df = df.drop(drop_cols, axis=1)


    df = df[["sum_asset_bought_zscore","num_of_trades_bought_zscore","sum_asset_sold_zscore","num_of_trades_sold_zscore","sum_asset_bought","num_of_trades_bought","sum_asset_sold","num_of_trades_sold"]]

    hueristic_df = df.loc[signal_index-pd.Timedelta(seconds=10):signal_index+pd.Timedelta(seconds=10)]

    print("> Hueristic df: ", hueristic_df)
    hueristic_df.to_csv("hueristic_df.csv")
    return hueristic_df



from sklearn.linear_model import LinearRegression
import numpy as np

def get_slope(prices):
    model = LinearRegression()
    x = np.arange(len(prices)).reshape(-1, 1)
    y = prices.reshape(-1, 1)
    model.fit(x, y)
    return model.coef_[0][0]

def evaluate_entry(prices, w1=1, w2=1, w3=1):
    # Ensure the input DataFrame has the required 'price' column
    
    # Calculating returns
    returns = prices.pct_change().dropna()
    
    # Ensure the first entry is not NaN due to pct_change
    prices = prices.dropna()
    
    # Calculated metrics
    metrics = {}
    
    # Modified Sharpe Ratio
    mean_return = returns.mean()
    std_dev = returns.std()
    metrics['sharpe_ratio'] = mean_return / std_dev if std_dev != 0 else np.nan
    
    # Modified Sortino Ratio
    negative_returns = returns[returns < 0]
    downside_std = negative_returns.std()
    metrics['sortino_ratio'] = mean_return / downside_std if downside_std != 0 else np.nan
    
    # Modified Calmar Ratio
    cumulative_returns = (returns + 1).cumprod()
    running_max = np.maximum.accumulate(cumulative_returns)
    drawdown = (running_max - cumulative_returns) / running_max
    max_drawdown = drawdown.max()
    metrics['calmar_ratio'] = mean_return / max_drawdown if max_drawdown != 0 else np.nan
    
    return metrics

SYMBOLS = [
    # "BTCUSDT",
    # "ETHUSDT",
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
    "TRBUSDT",
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
    "FOOTBALLUSDT",
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
    "MAVUSDT",
    "MDTUSDT",
    "XVGUSDT",
    "WLDUSDT",
    "PENDLEUSDT",
    "ARKMUSDT",
    "AGLDUSDT",
    "YGGUSDT",
    "DODOXUSDT",
    "BNTUSDT",
    "OXTUSDT",
    "SEIUSDT",
    "CYBERUSDT",
    "HIFIUSDT",
    "ARKUSDT",
    "FRONTUSDT",
    "GLMRUSDT",
    "BICOUSDT"
]



# SYMBOLS = ["SOLUSDT", "COMPUSDT", "SNXUSDT", "STORJUSDT", "XLMUSDT", "XRPUSDT"]
# all_ideal_trades_df = pd.DataFrame()

# for month in ["2023-06", "2023-07", "2023-08"]:
#     for symbol in SYMBOLS:
#         try:
#             print("********")
#             print("> Processing symbol: ", symbol, month)

#             df = add_ideal_trade_column(symbol, month)
#             df.index = pd.to_datetime(df.index)

#             ideal_trade_df = df[df['isIdealTrade'] == 1]
#             not_ideal_trade_df = df[df['isIdealTrade'] == 0]

#             not_ideal_sample = not_ideal_trade_df.sample(n=len(ideal_trade_df), random_state=42)


#             all_ideal_trades_df = pd.concat([all_ideal_trades_df, ideal_trade_df], ignore_index=True)
#             all_ideal_trades_df = pd.concat([all_ideal_trades_df, not_ideal_sample], ignore_index=True)
#             all_ideal_trades_df.to_csv("all_ideal_trades.csv")

#         except Exception as e:
#             print("Global exception: ", e)
            # continue

    # # print("> Length of ideal trades: ", len(ideal_trade_df))
    # # print("> Length of non ideal trades: ", len(not_ideal_trade_df))


    # # print("> Ideal total_z_score mean: ", ideal_trade_df.total_z_score.mean())
    # # print("> Non ideal total_z_score mean: ", not_ideal_trade_df.total_z_score.mean())

    # # high_zscore_non_ideal_df = not_ideal_trade_df[not_ideal_trade_df['total_z_score'] > 33.31]
    # # print("> Length of high zscore non ideal trades: ", len(high_zscore_non_ideal_df))
    # total = 0


symbol = "APTUSDT"
month = "2023-08"
signal_col = "high_zscore"

df = RetriveDataset(symbol, month).retrieve_trading_dataset()
df = add_signal_column(df, signal_col)




# trading_data = RetriveDataset(symbol, month)

# df = trading_data.retrieve_trading_dataset()

while True:
    # Get locations of where signal is 1 or -1
    signals = df[df[signal_col] == 1].index

    if len(signals) == 0:
        break

    signal_index = signals[0]
    print("********")
    print("> Signal index: ", signal_index)

    get_ideal_trade_surronding_data(df, signal_index)
    hueristic_df = df.loc[signal_index:signal_index+pd.Timedelta(minutes=65)]

    plot_df = df.loc[signal_index-pd.Timedelta(minutes=5):signal_index+pd.Timedelta(minutes=65)]

    plot_data(plot_df, symbol, signal_to_plot=signal_col, signal_index=signal_index, plot_folder="ideal_trades")
    df = df.loc[signal_index+pd.Timedelta(minutes=65):]



    # print("> Total: ", total)
    # exit()