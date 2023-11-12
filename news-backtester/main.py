# The second attempt of making a main file for the backtester
# I want to make a  function or class that brings in data for a symbol
# Then adds a entry signal and exit signal
# Runs the backtester and measure the results
# The entry and exit signals will be programable and will changed via interation

# Entry signal variables:
# time_from_news_signal: 10 
# sum_asset_sold_zscore: 100


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
import hashlib

load_dotenv()

LOCAL_LOCATION = os.getenv("LOCAL_LOCATION")

CONFIG = {
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
    ]
}

SIGNAL_VARIABLES = {
    "entry" :{
        "time_from_news_signal": 10,
        "sum_asset_sold_zscore": 110, 
    }, 
    "exit": {
        "buy_sold_ratio": 1.3,
    }, 
    "features": {
        "num_trade_ema_span": 5,
    }
}

class BacktesterData():

    def __init__(self, symbol, date, should_plot=False, verbose=False):

        self.trade_run_data = {
            "symbol": symbol,
            "date": date,
            "signal_variables": SIGNAL_VARIABLES,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_gain_loss_percentage": 0,
            "average_gain_loss_percentage": 0,
            "max_potentional_gain_loss_percentage": 0,
            "trades": []
        }
        self.symbol = symbol
        self.date = date
        self.verbose = verbose
        self.last_trade_index = None
        self.dataset_filename = f"{symbol}_{date.replace('-', '_')}.csv"

        # Checks if should load from cache
        if self.dataset_filename in os.listdir('local/datasets'):
            # Loading from a csv file to save dev time
            self.symbol_dataset = pd.read_csv(f'local/datasets/{self.dataset_filename}', index_col=0, parse_dates=True)
        else:
            symbol_retriever = RetriveDataset(symbol, date, copy.deepcopy(CONFIG))
            self.symbol_dataset = symbol_retriever.retrieve_trading_dataset()
            if self.symbol_dataset is None:
                return
            self.symbol_dataset.to_csv(f'local/datasets/{self.dataset_filename}')

        
        if self.symbol_dataset is None:
            print(f"> No data for {symbol} on {date}")
            return

        num_trade_ema_span = SIGNAL_VARIABLES["features"]["num_trade_ema_span"]

        self.symbol_dataset['num_of_trades_sold_ema'] = round(self.symbol_dataset['num_of_trades_sold'].ewm(span=num_trade_ema_span, adjust=False, min_periods=num_trade_ema_span).mean(), 2)
        self.symbol_dataset['num_of_trades_bought_ema'] = round(self.symbol_dataset['num_of_trades_bought'].ewm(span=num_trade_ema_span, adjust=False, min_periods=num_trade_ema_span).mean(), 2)

        self.symbol_dataset['sum_of_trades_sold_ema'] = round(self.symbol_dataset['sum_asset_sold'].ewm(span=num_trade_ema_span, adjust=False, min_periods=num_trade_ema_span).mean(), 2)
        self.symbol_dataset['sum_of_trades_bought_ema'] = round(self.symbol_dataset['sum_asset_bought'].ewm(span=num_trade_ema_span, adjust=False, min_periods=num_trade_ema_span).mean(), 2)
        
        self.symbol_dataset['num_of_trades_sold_zscore_ema'] = round(self.symbol_dataset['num_of_trades_sold_zscore'].ewm(span=7, adjust=False, min_periods=7).mean(), 2)
        self.symbol_dataset['num_of_trades_bought_zscore_ema'] = round(self.symbol_dataset['num_of_trades_bought_zscore'].ewm(span=7, adjust=False, min_periods=7).mean(), 2)

        self.symbol_dataset['sum_of_trades_sold_zscore_ema'] = round(self.symbol_dataset['sum_asset_sold_zscore'].ewm(span=7, adjust=False, min_periods=7).mean(), 2)
        self.symbol_dataset['sum_of_trades_bought_zscore_ema'] = round(self.symbol_dataset['sum_asset_bought_zscore'].ewm(span=7, adjust=False, min_periods=7).mean(), 2)


        self.symbol_dataset = self.add_entry_signal(self.symbol_dataset)
        

        if should_plot:
            signals_to_plot = ['news_signal', 'entry_signal']
            plot_data(self.symbol_dataset, symbol, signals_to_plot=signals_to_plot, title="APT_2023_09")


    def add_entry_signal(self, df):
        news_seconds_variable = SIGNAL_VARIABLES["entry"]["time_from_news_signal"]
        sum_asset_sold_zscore_variable = SIGNAL_VARIABLES["entry"]["sum_asset_sold_zscore"]

        print("> Adding entry signal")
        print(f"> Seconds from news: {news_seconds_variable} seconds", )
        print(f"> Sum asset sold zscore threshold: {sum_asset_sold_zscore_variable}")

        df["entry_signal"] = 0
        df['news_signal_past'] = df['news_signal'].rolling(window=news_seconds_variable).max()

        mask = (
            (df['sum_asset_sold_zscore'] > sum_asset_sold_zscore_variable) & 
            (df['news_signal_past'] == 1)
        )

        df.loc[mask, 'entry_signal'] = 1

        print("> Entry signal added")
        amount_of_signals = len(df[df['entry_signal'] == 1])
        print(f"> Amount of entry signals: {amount_of_signals}")
        return df
    

    def backtest_trades(self):

        df = self.symbol_dataset.copy()

        bought_sold_ratio_threshold = SIGNAL_VARIABLES["exit"]["buy_sold_ratio"]

        print("> Adding exit signal")
        print(f"> Buy sold ratio threshold: {bought_sold_ratio_threshold}")

        entry_signals = df[df['entry_signal'] == 1]

        # Adds total trades
        self.trade_run_data["total_trades"] = len(entry_signals)

        # Iterate through entry signals
        for signal_index, signal_row in entry_signals.iterrows():

            # Skip if entry signal is within 20 minutes of last trade
            if self.last_trade_index is not None:
                if signal_index - self.last_trade_index < pd.Timedelta(minutes=20):
                    continue
            
            self.last_trade_index = signal_index

            entry_price = signal_row['avg_price']

            if self.verbose:
                print("-----")
                print(f"Entry signal at {signal_index}")
                print(f"Entry price: {entry_price}")

            signal_df = df.loc[signal_index-pd.Timedelta(seconds=10):signal_index+pd.Timedelta(minutes=60)]
            past_signal, trade_finished = False, False
            time_in_trade = 0

            trade_data = {
                "entry_price": entry_price,
                "signal_index": str(signal_index),
                "exit_price": None,
                "exit_price_diff": 0,
                "exit_index": "",
                "max_price_diff": 0,
                "time_in_trade": 0,
                "news_index": None,
                "potential_max_price_diff": 0, 
                "potential_max_price_diff_index": ""
            }

            for index, row in signal_df.iterrows():
                num_bought_ema = row['num_of_trades_bought_ema']
                num_sold_ema = row['num_of_trades_sold_ema']

                sum_bought_ema = row['sum_of_trades_bought_ema']
                sum_sold_ema = row['sum_of_trades_sold_ema']

                if num_sold_ema != 0 and num_bought_ema != 0:
                    bought_sold_ratio = round(num_bought_ema / num_sold_ema, 2)
                else:
                    bought_sold_ratio = 1

                if sum_sold_ema != 0 and sum_bought_ema != 0:
                    sum_bought_sold_ratio = round(sum_bought_ema / sum_sold_ema, 2)
                else:
                    sum_bought_sold_ratio = 1
                

                price_diff = round((row['avg_price'] - entry_price) / entry_price, 4)

                if signal_index == index:
                    past_signal = True
                    # print(f"{index}: {row['avg_price']} <--- SIGNAL Entry price")
                else:
                    if row["news_signal"] == 1:
                        trade_data["news_index"] = str(index)

                if past_signal:
                    time_in_trade += 1
                    trade_data["max_price_diff"] = max(trade_data["max_price_diff"], price_diff)
                
                if self.verbose:
                    message = f"sum_asset_bought_zscore: {row['sum_asset_bought_zscore']}, num_of_trades_bought_zscore: {row['num_of_trades_bought_zscore']}, sum_asset_sold_zscore: {row['sum_asset_sold_zscore']}, num_of_trades_sold_zscore: {row['num_of_trades_sold_zscore']}"
                    # message = f"num_bought_ema: {num_bought_ema}, num_sold_ema: {num_sold_ema}, sum_bought_ema: {sum_bought_ema}, sum_sold_ema: {sum_sold_ema}, "

                    if past_signal:
                        message += f", bought_sold_ratio: {bought_sold_ratio}, sum_bought_sold_ratio: {sum_bought_sold_ratio}, price_diff: {price_diff}"

                    if signal_index == index:
                        message += " <--- SIGNAL Entry price"

                    if (past_signal and not trade_finished) and bought_sold_ratio > bought_sold_ratio_threshold:
                        message += " <--- SIGNAL Exit price"

                    print(f"> {index}: {message}")      

                # Eligible and passes threshold
                if (past_signal and not trade_finished) and bought_sold_ratio > bought_sold_ratio_threshold:
                    exit_price = row['avg_price']

                    trade_data["exit_price"] = exit_price
                    trade_data["exit_price_diff"] = price_diff
                    trade_data["time_in_trade"] = time_in_trade
                    trade_data["exit_index"] = str(index)

                    if price_diff > 0:
                        self.trade_run_data["winning_trades"] += 1
                    else:
                        self.trade_run_data["losing_trades"] += 1

                    self.trade_run_data["total_gain_loss_percentage"] += price_diff
                    self.trade_run_data["average_gain_loss_percentage"] = round(self.trade_run_data["total_gain_loss_percentage"] / self.trade_run_data["total_trades"], 4)
                    
                    trade_finished = True

                if trade_finished:
                    last_potential = trade_data["potential_max_price_diff"]
                    trade_data["potential_max_price_diff"] = max(last_potential, price_diff)

                    if trade_data["potential_max_price_diff"] != last_potential:
                        trade_data["potential_max_price_diff_index"] = str(index)

                if self.verbose:
                    time.sleep(1)

            self.trade_run_data["max_potentional_gain_loss_percentage"] += trade_data["potential_max_price_diff"]
            
            self.trade_run_data["trades"].append(trade_data)


    def save_trade_run_data(self):
        print("> Saving trade run data")

        hash_str = self.hash_dict_to_string(SIGNAL_VARIABLES)

        print(f"> Saving to results/{self.date}/{hash_str}/trade_run_{self.symbol}_{self.date}.json")

        with open(f"results/{self.date}/{hash_str}/trade_run_{self.symbol}_{self.date}.json", "w") as f:
            json.dump(self.trade_run_data, f, indent=4)

        print("> Trade run data saved")


    def hash_dict_to_string(self, d):
        serialized_dict = json.dumps(d, sort_keys=True).encode('utf-8')
        
        hash_object = hashlib.sha256(serialized_dict)
        hash_hex = hash_object.hexdigest()
        
        return str(hash_hex)[-5:]
    

    def remove_symbol_dataset(self):
        try:
            os.remove(f'local/datasets/{self.dataset_filename}')    
        except:
            print("> No dataset to remove")



with open("symbols.json", "r") as f:
    symbols = json.load(f)

# 2023-09 Symbols
# symbols = [
#     "ACHUSDT",
#     "ANKRUSDT",
#     "APTUSDT",
#     "ASTRUSDT",
#     "CHZUSDT",
#     "CTKUSDT",
#     "CTSIUSDT",
#     "DGBUSDT",
#     "GALUSDT",
#     "HFTUSDT",
#     "ICXUSDT",
#     "IDUSDT",
#     "KLAYUSDT",
#     "LEVERUSDT",
#     "MATICUSDT",
#     "MDTUSDT",
#     "MINAUSDT",
#     "MTLUSDT",
#     "ONEUSDT",
#     "ROSEUSDT",
#     "STGUSDT",
#     "SUIUSDT",
#     "UMAUSDT",
#     "ZENUSDT"
# ]

def hash_dict_to_string(d):
    serialized_dict = json.dumps(d, sort_keys=True).encode('utf-8')
    
    hash_object = hashlib.sha256(serialized_dict)
    hash_hex = hash_object.hexdigest()
    
    return str(hash_hex)[-5:]


# Interating over varibales
num_trade_ema_spans = [2, 3, 4, 5, 10, 15, 20, 40, 80]
num_trade_ema_spans = [2, 3, 4, 5]
buy_sold_ratios = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.2]

num_trade_ema_spans = [2]
buy_sold_ratios = [1]

# buy_sold_ratios = [0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3, 1.5, 2]
date = "2023-10"

for symbol in symbols:
    already_ran = False
    for num_trade_ema_span in num_trade_ema_spans:
        for buy_sold_ratio in buy_sold_ratios:
            
            print("> Running backtest for symbol: ", symbol)

            SIGNAL_VARIABLES = {
                "entry" :{
                    "time_from_news_signal": 10,
                    "sum_asset_sold_zscore": 90, 
                }, 
                "exit": {
                    "buy_sold_ratio": buy_sold_ratio,
                }, 
                "features": {
                    "num_trade_ema_span": num_trade_ema_span,
                }
            }

            variables_hash_str = hash_dict_to_string(SIGNAL_VARIABLES)
            
            print(f"> num_trade_ema_span: {num_trade_ema_span}, buy_sold_ratio: {buy_sold_ratio}")
            print(f"> variables_hash_str: {variables_hash_str}")

            if not os.path.exists(f"results/{date}/{variables_hash_str}/"):
                os.makedirs(f"results/{date}/{variables_hash_str}/")

            if not os.path.exists(f"results/{date}/{variables_hash_str}/overall_results.json"):
                OVERALL_RESULTS = {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "total_gain_loss_percentage": 0,
                    "average_gain_loss_percentage": 0,
                    "max_potentional_gain_loss_percentage": 0,
                    "symbols_contributing": [],
                    "SIGNAL_VARIABLES": SIGNAL_VARIABLES
                }
            else:
                with open(f"results/{date}/{variables_hash_str}/overall_results.json", "r") as f:
                    OVERALL_RESULTS = json.load(f)
                
            if symbol in OVERALL_RESULTS["symbols_contributing"]:
                print("> Already ran this symbol")
                already_ran = True
                continue

            bt = BacktesterData(symbol, date)
            if bt.symbol_dataset is None:
                continue
            bt.backtest_trades()
            
            if bt.trade_run_data["total_trades"] > 0:
                bt.save_trade_run_data()
            else:
                print("> No trades made")
            
            OVERALL_RESULTS["total_trades"] += bt.trade_run_data["total_trades"]
            OVERALL_RESULTS["winning_trades"] += bt.trade_run_data["winning_trades"]
            OVERALL_RESULTS["losing_trades"] += bt.trade_run_data["losing_trades"]
            OVERALL_RESULTS["total_gain_loss_percentage"] += bt.trade_run_data["total_gain_loss_percentage"]
            OVERALL_RESULTS["max_potentional_gain_loss_percentage"] += bt.trade_run_data["max_potentional_gain_loss_percentage"]
            OVERALL_RESULTS["symbols_contributing"].append(symbol)
            
            OVERALL_RESULTS["total_gain_loss_percentage"] = round(OVERALL_RESULTS["total_gain_loss_percentage"], 4)
            OVERALL_RESULTS["max_potentional_gain_loss_percentage"] = round(OVERALL_RESULTS["max_potentional_gain_loss_percentage"], 4)

            with open(f"results/{date}/{variables_hash_str}/overall_results.json", "w") as f:
                json.dump(OVERALL_RESULTS, f, indent=4)
            
    if already_ran:
        continue

    bt.remove_symbol_dataset()

# variables_hash_str = hash_dict_to_string(SIGNAL_VARIABLES)

# if not os.path.exists(f"results/{variables_hash_str}/"):
#     os.makedirs(f"results/{variables_hash_str}/")

# OVERALL_RESULTS = {
#     "total_trades": 0,
#     "winning_trades": 0,
#     "losing_trades": 0,
#     "total_gain_loss_percentage": 0,
#     "average_gain_loss_percentage": 0,
#     "max_potentional_gain_loss_percentage": 0,
#     "SIGNAL_VARIABLES": SIGNAL_VARIABLES
# }

# for symbol in symbols:
#     total_gain_loss_percentage = 0

#     bt = BacktesterData(symbol, "2023-09", should_plot=False)
#     bt.backtest_trades()
    
#     if bt.trade_run_data["total_trades"] > 0:
#         bt.save_trade_run_data()
#     else:
#         print("> No trades made")
    
#     OVERALL_RESULTS["total_trades"] += bt.trade_run_data["total_trades"]
#     OVERALL_RESULTS["winning_trades"] += bt.trade_run_data["winning_trades"]
#     OVERALL_RESULTS["losing_trades"] += bt.trade_run_data["losing_trades"]
#     OVERALL_RESULTS["total_gain_loss_percentage"] += bt.trade_run_data["total_gain_loss_percentage"]
#     OVERALL_RESULTS["max_potentional_gain_loss_percentage"] += bt.trade_run_data["max_potentional_gain_loss_percentage"]


# with open(f"results/{variables_hash_str}/overall_results.json", "w") as f:
#     json.dump(OVERALL_RESULTS, f, indent=4)    





