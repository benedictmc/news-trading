import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from plot_data import plot_data

class Backtester():

    def __init__(self, data, symbol, date, inital_capital=100000):
        print("=== Backtester ===")
        print("> Initialising backtester...")
        self.data = data
        self.inital_capital = inital_capital
        self.symbol = symbol
        self.date = date
        self.total_trade_score = 0
        self.positive_trades = 0
        self.negative_trades = 0

        # Check if index is datetime
        if not isinstance(self.data.index, pd.Timestamp):
            self.data.index = pd.to_datetime(self.data.index, format='%Y-%m-%d %H:%M:%S')
        
        self.data.sort_index(inplace=True)
        self.start_time = self.data.index[0]
        self.end_time = self.data.index[-1]
        self.trade_number = 0

        self.trade_list = []


    def run(self, should_plot=False):
        while True:

            # Get locations of where signal is 1 or -1
            signals = self.data[self.data['signal'].isin([-1, 1])].index

            if len(signals) == 0:
                print("> No more signals found")
                break

            # Hack to check if news signal is 1 5 mins before/after the signal
            signal_index = signals[0]
            signal_row = self.data.loc[signal_index]

            # print(f"> Signal found at: {signal_index}")

            trade_dict = self.__create_trade_dict(signal_index, signal_row)

            # Create dataframe from the first signal onwards
            signal_df = self.data.loc[signal_index:signal_index+pd.Timedelta(minutes=60)]
            
            # Check if new signal is in the df for the last one minute
            # print("=====================================")
            # print("> News signal found")
        
            time_past = 0
            max_pos_pct_change, max_neg_pct_change = -99999, 99999
            entry_price = trade_dict["entry_price"]
            max_price, min_price = entry_price, entry_price

            entry_price = trade_dict["entry_price"]

            for index, row in signal_df.iterrows():
                
                current_price = row['avg_price']

                max_price = max(max_price, current_price)
                min_price = min(min_price, current_price)
                trade_dict["max_price"] = max_price
                trade_dict["min_price"] = min_price

                pct_change = round((current_price - entry_price) / entry_price, 6)
                max_pos_pct_change = round(max(max_pos_pct_change, pct_change), 6)

                if trade_dict["max_pos_pct_change"] != max_pos_pct_change:

                    trade_dict.update({
                        "max_pos_pct_change": max_pos_pct_change,
                        "max_pos_pct_change_time": str(index),
                    })

                max_neg_pct_change = round(min(max_neg_pct_change, pct_change), 6)

                if trade_dict["max_neg_pct_change"] != max_neg_pct_change:
                    trade_dict.update({
                        "max_neg_pct_change": max_neg_pct_change,
                        "max_neg_pct_change_time": str(index),
                    })

            trade_dict["end_price"] = current_price
            trade_dict["end_time"] = str(index)

            trade_dict["trade_score"] = round((trade_dict["max_pos_pct_change"] + trade_dict["max_neg_pct_change"]), 6)

            self.total_trade_score += trade_dict["trade_score"]
            if trade_dict["trade_score"] > 0:
                self.positive_trades += 1
            else:
                self.negative_trades += 1

            self.trade_list.append(trade_dict)

            if should_plot:
                plot_df = self.data.loc[signal_index-pd.Timedelta(minutes=10):signal_index+pd.Timedelta(minutes=60)]
                plot_title = f"Trade at {signal_index}; Max Positive change: {max_pos_pct_change}; Max Negative change: {max_neg_pct_change}"

                plot_data(plot_df, self.symbol, 'signal', title=plot_title, signal_index=signal_index)

            self.trade_number += 1

            post_cooldown_index = signal_index+pd.Timedelta(minutes=80)
            self.data = self.data.loc[post_cooldown_index:]

            # print(f"> Ending trade at {index}")
            # print(f"> Max positive price change is {max_pos_pct_change}")
            # print(f"> Max negative price change is {max_neg_pct_change}")

            # print(f"> Starting new dataframe at {post_cooldown_index}")
            # print("=====================================")
            # exit()
        return


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


    def __create_trade_dict(self, signal_index, signal_row):

        trade_dict = {}
        # Set TP and SL prices
        tp = 0.03 # 3%
        sl = 0.01 # 1%

        position_type = 'long' if signal_row['signal'] == 1 else 'short'
        entry_price = signal_row['avg_price']
        
        tp_multiplier = 1 + tp  if position_type == 'long' else 1 - tp
        sl_multiplier = 1 - sl if position_type == 'long' else 1 + sl


        trade_dict["trade_time"] = str(signal_index)
        trade_dict["trade_number"] = self.trade_number
        trade_dict["symbol"] = self.symbol
        trade_dict["position_type"] = 'long' if signal_row['signal'] == 1 else 'short'
        trade_dict["entry_price"] = signal_row['avg_price']
        
        trade_dict["tp_price"] = trade_dict["entry_price"] * tp_multiplier
        trade_dict["sl_price"] = trade_dict["entry_price"] * sl_multiplier
        trade_dict["tp_price_hit"] = False
        trade_dict["sl_price_hit"] = False
        trade_dict["max_pos_pct_change"] = -1
        trade_dict["max_neg_pct_change"] = 1

        # print(f"> Starting {position_type} position at {entry_price}")
        # print(f"> Starting trade at {signal_index}")

        return trade_dict



