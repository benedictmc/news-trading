import backtrader as bt
import pandas as pd
import time
import matplotlib.pyplot as plt
import os
import json


class Backtester():

    def __init__(self, data, singal_window, signal_threshold, inital_capital):
        self.data = data
        self.inital_capital = inital_capital
        self.signal_window = singal_window
        self.signal_threshold = signal_threshold

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
                print("No signals found")
                break

            trade_dict = {}
            # Create dataframe from the first signal onwards
            signal_df = self.data.loc[signals[0]:]
            signal_row = signal_df.iloc[0]
            trade_index = signal_df.index[0]

            position_type = 'long' if signal_row['signal'] == 1 else 'short'
            entry_price = signal_row['avg_price']

            trade_dict["trade_time"] = str(trade_index)
            trade_dict["trade_number"] = self.trade_number
            trade_dict["symbol"] = symbol
            trade_dict["window_start_time"] = str(trade_index - pd.Timedelta(seconds=self.signal_window))
            trade_dict["position_type"] = 'long' if signal_row['signal'] == 1 else 'short'
            trade_dict["entry_price"] = signal_row['avg_price']
            trade_dict["sl_price"] = trade_dict["entry_price"] * 0.975
            trade_dict["tp_price"] = trade_dict["entry_price"] * 1.05


            print(f"> Starting {position_type} position at {entry_price}")
            print(f"> Starting trade at {trade_index}")

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
                
                print("***********")
                print(f"> Entry price is {entry_price} after {time_past} seconds. Type is {position_type}")
                print(f"> Current price is {row['avg_price']}")
                print(f"> Current pct change is {pct_change}")
                print(f"> Stop loss price is {trade_dict['sl_price']}")
                print(f"> Take profit price is {trade_dict['tp_price']}")
                print(f"> Number of buy trades is {row.num_of_trades_bought}")
                print(f"> Number of sell trades is {row.num_of_trades_sold}")
                print(f"Volume of asset bought is {row.sum_asset_bought}")
                print(f"Volume of asset sold is {row.sum_asset_sold}")

                print(f"> Number of buy trades is {row.num_of_trades_bought}")

                time.sleep(1)
                time_past += 1
                
                # Break trade if time_past is 5 minutes
                if time_past == (60*5):
                    break
            
            trade_dict["end_price"] = row['avg_price']
            trade_dict["end_time"] = str(index)
            self.trade_list.append(trade_dict)
            
            self.plot_trade(trade_index, entry_price, symbol, position_type, trade_dict)
            self.trade_number += 1

            post_cooldown_index = index+pd.Timedelta(minutes=80)
            self.data = self.data.loc[post_cooldown_index:]
            
            print(f"> Ending trade at {index}")
            print(f"> Max positive price change is {max_pos_pct_change}")
            print(f"> Max negative price change is {max_neg_pct_change}")

            print(f"> Starting new dataframe at {post_cooldown_index}")
            print("=====================================")

        return

    def plot_trade(self, trade_index, entry_price, symbol, position_type, trade_dict):
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

            singal_window_index = trade_index - pd.Timedelta(seconds=self.signal_window)

            plt.scatter(singal_window_index, trade_data.loc[singal_window_index, 'avg_price'], color='yellow', marker='*', s=100, label='Window Start')

            plt.axhline(y=entry_price, color='g', linestyle='--', label='Entry price')
            plt.title(f'{position_type} Trade at {trade_index}')
            plt.xlabel('Time')
            plt.ylabel('Average Price')
            plt.legend()
            plt.grid(True)
            results_folder = f'local/results/{symbol}/sw_{signal_window}_st_{signal_threshold}_{date}/'

            if not os.path.exists(results_folder):
                os.makedirs(results_folder)
            print(f"Saving plot to {results_folder}trade_{self.trade_number}.png")

            plt.savefig(f'{results_folder}trade_{self.trade_number}.png')
        except:
            print(trade_data.head())


    def save_trade_list(self):
        if self.trade_list == []:
            print("No trades found")
            return
        
        results_folder = f'local/results/{symbol}/sw_{signal_window}_st_{signal_threshold}_{date}/'
        
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

date = "2023-07"
symbol = "BTCUSDT"

signal_window = 50
signal_threshold = 0.005
df = RetriveDataset(symbol, date, signal_window, signal_threshold, load_source="blob").retrieve_trading_dataset()
# df = df[['floored_time', 'avg_price', 'signal']]

df['floored_time'] = pd.to_datetime(df['floored_time'], format='%Y-%m-%d %H:%M:%S')

# Drop rows with NaN values
df.dropna(inplace=True)

# Replace NaN or Inf with 0
df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)

df.set_index('floored_time', inplace=True)

backtester = Backtester(df, signal_window, signal_threshold, 10000)
backtester.run()
backtester.save_trade_list()




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




