import backtrader as bt
import pandas as pd
import time
import matplotlib.pyplot as plt
import os
import json


class Backtester():

    def __init__(self, data, symbol, date, inital_capital=100000):
        print("=== Backtester ===")
        print("> Initialising backtester...")
        self.data = data
        self.inital_capital = inital_capital
        self.symbol = symbol
        self.date = date

        # Check if index is datetime
        if not isinstance(self.data.index, pd.Timestamp):
            self.data.index = pd.to_datetime(self.data.index, format='%Y-%m-%d %H:%M:%S')
        
        self.data.sort_index(inplace=True)
        self.start_time = self.data.index[0]
        self.end_time = self.data.index[-1]
        self.trade_number = 0

        self.trade_list = []


    def run(self):

        while True:
            # Get locations of where signal is 1 or -1
            signals = self.data[self.data['signal'].isin([-1, 1])].index

            if len(signals) == 0:
                print("> No more signals found")
                break

            # Hack to check if news signal is 1 5 mins before/after the signal
            signal_index = signals[0]

            print(f"> Signal found at: {signal_index}")

            trade_dict = {}
            # Create dataframe from the first signal onwards
            signal_df = self.data.loc[signal_index:]
            signal_row = signal_df.iloc[0]

            # Check if new signal is in the df for the last one minute
            
            print("=====================================")
            print("> News signal found")
            print(signal_index)

            position_type = 'long' if signal_row['signal'] == 1 else 'short'
            entry_price = signal_row['avg_price']
            tp_multiplier = 1.05 if position_type == 'long' else 0.95
            sl_multiplier = 0.975 if position_type == 'long' else 1.025


            trade_dict["trade_time"] = str(signal_index)
            trade_dict["trade_number"] = self.trade_number
            trade_dict["symbol"] = self.symbol
            trade_dict["position_type"] = 'long' if signal_row['signal'] == 1 else 'short'
            trade_dict["entry_price"] = signal_row['avg_price']
            
            trade_dict["tp_price"] = trade_dict["entry_price"] * tp_multiplier
            trade_dict["sl_price"] = trade_dict["entry_price"] * sl_multiplier
            trade_dict["tp_price_hit"] = False
            trade_dict["sl_price_hit"] = False

            print(f"> Starting {position_type} position at {entry_price}")
            print(f"> Starting trade at {signal_index}")

            time_past = 0
            max_pos_pct_change = -99999
            max_neg_pct_change = 99999

            for index, row in signal_df.iterrows():

                pct_change = round((row['avg_price'] - entry_price) / entry_price, 6)

                current_max_pos_pct_change = max_pos_pct_change
                max_pos_pct_change = max(max_pos_pct_change, pct_change)

                current_max_neg_pct_change = max_neg_pct_change
                max_neg_pct_change = min(max_neg_pct_change, pct_change)
                
                if current_max_pos_pct_change != max_pos_pct_change:
                    trade_dict["max_pos_pct_change"] = max_pos_pct_change
                    trade_dict["max_pos_pct_change_time"] = str(index)
                    trade_dict["max_pos_pct_change_time_past"] = time_past

                if current_max_neg_pct_change != max_neg_pct_change:
                    trade_dict["max_neg_pct_change"] = max_neg_pct_change
                    trade_dict["max_neg_pct_change_time"] = str(index)
                    trade_dict["max_neg_pct_change_time_past"] = time_past
                
                # Check if TP or SL is hit
                if not trade_dict["sl_price_hit"] and not trade_dict["tp_price_hit"]:
                    if position_type == 'long' and row['avg_price'] >= trade_dict["tp_price"] or position_type == 'short' and row['avg_price'] <= trade_dict["tp_price"]:
                        trade_dict["tp_price_hit"] = True
                        trade_dict["tp_price_hit_time"] = str(index)    
                        break

                if not trade_dict["sl_price_hit"] and not trade_dict["tp_price_hit"]:
                    if position_type == 'long' and row['avg_price'] <= trade_dict["sl_price"] or position_type == 'short' and row['avg_price'] >= trade_dict["sl_price"]:
                        trade_dict["sl_price_hit"] = True
                        trade_dict["sl_price_hit_time"] = str(index)
                        break

                time_past += 1
                
                # Break trade if time_past is 5 minutes
                if time_past == (60*10):
                    print("> Trade has been running for 10 minutes, breaking trade")
                    trade_dict["end_pct_change"] = pct_change
                    if position_type == 'long' and row['avg_price'] > entry_price or position_type == 'short' and row['avg_price'] < entry_price:
                        trade_dict["end_outcome"] = "positive"
                    else:
                        trade_dict["end_outcome"] = "negative"
                    break
            
            trade_dict["end_price"] = row['avg_price']
            trade_dict["end_time"] = str(index)
            self.trade_list.append(trade_dict)
            
            self.plot_trade(signal_index, entry_price, position_type, trade_dict)

            # Save trade data to CSV
            # trade_df = self.data.loc[signal_index-pd.Timedelta(minutes=1):signal_index+pd.Timedelta(minutes=10)]
            # trade_df.to_csv(f'local/results/{self.symbol}/sw_{self.signal_window}_st_{self.signal_threshold}_{self.date}/trade_{self.trade_number}.csv')

            self.trade_number += 1

            post_cooldown_index = signal_index+pd.Timedelta(minutes=80)
            self.data = self.data.loc[post_cooldown_index:]
            
            print(f"> Ending trade at {index}")
            print(f"> Max positive price change is {max_pos_pct_change}")
            print(f"> Max negative price change is {max_neg_pct_change}")

            print(f"> Starting new dataframe at {post_cooldown_index}")
            print("=====================================")

        return

    def plot_trade(self, trade_index, entry_price, position_type, trade_dict):
        try:
            pre_trade_index = trade_index - pd.Timedelta(minutes=30)
            post_trade_index = trade_index + pd.Timedelta(minutes=30)

            # Plot avg_price over the time of the trade
            trade_data = self.data.loc[pre_trade_index:post_trade_index]

            max_pos_pct_change_time = pd.to_datetime(trade_dict["max_pos_pct_change_time"], format='%Y-%m-%d %H:%M:%S')
            max_neg_pct_change_time = pd.to_datetime(trade_dict["max_neg_pct_change_time"], format='%Y-%m-%d %H:%M:%S')

            # Plot avg_price over the time of the trade
            plt.figure(figsize=(10,6))
           
            plt.plot(trade_data.index, trade_data['avg_price'], label='avg_price', color='blue')

            # Add red triangle marker at the index of the signal
            plt.scatter(trade_index, trade_data.loc[trade_index, 'avg_price'], color='red', marker='^', s=100, label='Signal')

            plt.scatter(max_pos_pct_change_time, trade_data.loc[max_pos_pct_change_time, 'avg_price'], color='blue', marker='^', s=100, label='Largest Positive Change')

            plt.scatter(max_neg_pct_change_time, trade_data.loc[max_neg_pct_change_time, 'avg_price'], color='pink', marker='^', s=100, label='Largest Negative Change')

            # Plot news signals
            signal_data = trade_data[trade_data['news_signal'] == 1]

            if not signal_data.empty:
                plt.scatter(signal_data.index, signal_data['avg_price'], color='orange', marker='o', s=20, label='News Signal')

            plt.axhline(y=entry_price, color='g', linestyle='--', label='Entry price')
            plt.title(f'{position_type} Trade at {trade_index}')
            plt.xlabel('Time')
            plt.ylabel('Average Price')
            plt.legend()
            plt.grid(True)
            results_folder = f'local/results/{self.symbol}/{self.date}/'

            if not os.path.exists(results_folder):
                os.makedirs(results_folder)
            print(f"> Saving plot to {results_folder}trade_{self.trade_number}.png")

            plt.savefig(f'{results_folder}trade_{self.trade_number}.png')
        except:
            print(trade_data.head())


    def save_trade_list(self):
        if self.trade_list == []:
            print("> No trades found")
            return
        
        results_folder = f'local/results/{self.symbol}/{self.date}/'
        
        best_outcome_pct = 0
        worst_outcome_pct = 0

        for trade in self.trade_list:
            if trade['position_type'] == 'long':
                best_outcome_pct += trade['max_pos_pct_change']
                worst_outcome_pct += trade['max_neg_pct_change']
            else:
                best_outcome_pct += -1*(trade['max_neg_pct_change'])
                worst_outcome_pct += -1*(trade['max_pos_pct_change'])

        self.trade_list.append({
            "best_outcome_pct": best_outcome_pct,
            "worst_outcome_pct": worst_outcome_pct,
            "trade_amount": len(self.trade_list),
        })

        if not os.path.exists(results_folder):
            os.makedirs(results_folder)

        with open(f'{results_folder}trade_list.json', 'w') as f:
            json.dump(self.trade_list, f, indent=4)

        best_outcome_pct = 0
        worst_outcome_pct = 0



from retrieve_dataset import RetriveDataset 

# date = "2023-08"
# self. = "LRCUSDT"

# signal_window = 50
# signal_threshold = 0.005
# df = RetriveDataset(symbol, date, signal_window, signal_threshold, load_source="blob").retrieve_trading_dataset()
# df = df[['floored_time', 'avg_price', 'signal']]

# ALL_SYMBOLS = [ 'BTCUSDT','ZECUSDT','EOSUSDT','SOLUSDT','XEMUSDT','OPUSDT','SNXUSDT','1INCHUSDT','TRXUSDT','QTUMUSDT','AGIXUSDT','RUNEUSDT','FLOWUSDT','BNBUSDT','HFTUSDT','APTUSDT','ANKRUSDT','DOGEUSDT','ASTRUSDT','RDNTUSDT','STXUSDT','CTKUSDT','ETHUSDT','NEARUSDT','TUSDT','IOTXUSDT','GRTUSDT','UNIUSDT','ZRXUSDT','DYDXUSDT','ICPUSDT','NEOUSDT','BNXUSDT','SANDUSDT','EGLDUSDT','SSVUSDT','GTCUSDT','MASKUSDT','AMBUSDT','DARUSDT','CELOUSDT','AAVEUSDT','HBARUSDT','ARBUSDT','SXPUSDT','ANTUSDT','ZENUSDT','ICXUSDT','XTZUSDT','YFIUSDT','RSRUSDT','PEOPLEUSDT','DGBUSDT','LINKUSDT','GALUSDT','FTMUSDT','FXSUSDT','TLMUSDT','CELRUSDT','SUSHIUSDT','ALPHAUSDT','ARPAUSDT','HOOKUSDT','MINAUSDT','COTIUSDT','JOEUSDT','ENSUSDT','WOOUSDT','INJUSDT','SKLUSDT','USDCUSDT','IMXUSDT','SFPUSDT','DASHUSDT','MAGICUSDT','PERPUSDT','CTSIUSDT','CHZUSDT','QNTUSDT','LEVERUSDT','IOTAUSDT','IOSTUSDT','WAVESUSDT','TOMOUSDT','BLZUSDT','C98USDT','VETUSDT','ZILUSDT','GMTUSDT','DOTUSDT','ROSEUSDT','LDOUSDT','XLMUSDT','CFXUSDT','LITUSDT','XVSUSDT','OCEANUSDT','BANDUSDT','HOTUSDT','LTCUSDT','AVAXUSDT','ENJUSDT','GALAUSDT','BATUSDT','FETUSDT','BALUSDT','FILUSDT','KAVAUSDT','RNDRUSDT','LPTUSDT','AUDIOUSDT','ALGOUSDT','XRPUSDT','OGNUSDT','GMXUSDT','ACHUSDT','ONTUSDT','KLAYUSDT','REEFUSDT','AXSUSDT','HIGHUSDT','LINAUSDT','ALICEUSDT','DUSKUSDT','FLMUSDT','PHBUSDT','ATOMUSDT','MATICUSDT','LQTYUSDT','STORJUSDT','CKBUSDT','KNCUSDT','MKRUSDT','APEUSDT','API3USDT','NKNUSDT','RVNUSDT','CHRUSDT','MANAUSDT','CRVUSDT','STMXUSDT','ADAUSDT','ATAUSDT','STGUSDT','ARUSDT','IDUSDT','RLCUSDT','THETAUSDT','BLURUSDT','ONEUSDT','TRUUSDT','TRBUSDT','COMPUSDT','IDEXUSDT','SUIUSDT','EDUUSDT','MTLUSDT','1000PEPEUSDT','1000FLOKIUSDT','DENTUSDT','BCHUSDT','1000XECUSDT','JASMYUSDT','UMAUSDT','BELUSDT','1000SHIBUSDT','RADUSDT','XMRUSDT','1000LUNCUSDT','SPELLUSDT','KEYUSDT','COMBOUSDT','UNFIUSDT','CVXUSDT','ETCUSDT','MAVUSDT','MDTUSDT','XVGUSDT','NMRUSDT','BAKEUSDT','WLDUSDT','PENDLEUSDT','ARKMUSDT','AGLDUSDT','YGGUSDT','SEIUSDT' ]

# SYMBOLS = [
#     "APTUSDT",
#     "ASTRUSDT",
#     "BALUSDT",
#     "BNBUSDT",
#     "C98USDT",
#     "CELOUSDT",
#     "CHZUSDT",
#     "CRVUSDT",
#     "DOGEUSDT",
# ]

SYMBOLS = [
    "GALUSDT",
    "GTCUSDT",
    "HBARUSDT",
    "HFTUSDT",
    "ICPUSDT",
    "INJUSDT",
    "KLAYUSDT",
    "LEVERUSDT",
    "MASKUSDT",
    "ONTUSDT",
    "QTUMUSDT",
    "RLCUSDT",
    "THETAUSDT",
    "XRPUSDT"
]
 

# for symbol in SYMBOLS:
#     print(f"> Running backtest for {symbol}")
#     trading_data = RetriveDataset(symbol, "2023-08", recompile=True)
#     trading_df = trading_data.retrieve_trading_dataset()

#     backtester = Backtester(trading_df, symbol, "2023-08", 10000)
#     backtester.run()
#     backtester.save_trade_list()

print(f"> Running backtest for {None}")
trading_data = RetriveDataset("BTCUSDT", "2023-08", recompile=True)
trading_df = trading_data.retrieve_trading_dataset()

backtester = Backtester(trading_df, "BTCUSDT", "2023-08", 10000)
backtester.run()
backtester.save_trade_list()

# Run Backtest
# for symbol in SYMBOLS:
#     print(f"> Running backtest for {symbol}")
#     trading_data = RetriveDataset(symbol, "2023-08", 5, 0.01)
#     trading_df = trading_data.retrieve_trading_dataset()

#     backtester = Backtester(trading_df, 5, 0.01, symbol, "2023-08", 10000)
#     backtester.run()
#     backtester.save_trade_list()




# for signal_window in [5, 10, 20, 30, 40, 50, 60, 120]:
#     for signal_threshold in [0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.06, 0.1]:
#         print(f"Running backtest for {symbol} with signal_window {signal_window} and signal_threshold {signal_threshold}")
#         df = RetriveDataset(symbol, date, signal_window, signal_threshold, load_source="blob").retrieve_trading_dataset()
#         df = df[['floored_time', 'avg_price', 'signal']]

#         df['floored_time'] = pd.to_datetime(df['floored_time'], format='%Y-%m-%d %H:%M:%S')

#         # Drop rows with NaN values
#         df.dropna(inplace=True)

#         # Replace NaN or Inf with 0
#         df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)

#         df.set_index('floored_time', inplace=True)

#         backtester = Backtester(df, signal_window, signal_threshold, 10000)
#         backtester.run()
#         backtester.save_trade_list()




