import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from retrieve_dataset import RetriveDataset
from backtest_trades import Backtester
import random
import json
import os
import plot_data

value_map = {}

def get_from_value_map(col, value_type):
    col_map = value_map.setdefault(col, {})
    return col_map.setdefault(value_type, None)

def save_to_value_map(col, value_type, value):
    value_map[col][value_type] = value


def evaluate_row(data_row):
    # Lists to store column names, values, z-scores, and percentiles
    cols = []
    values = []
    z_scores = []
    percentiles = []
    total_z_score = 0

    for col, value in data_row.items():
        if col in ["avg_price", "index", "news_signal", "signal"]:
            continue
                
        cols.append(col)
        values.append(str(value))  # Convert value to string for consistent formatting later

        if "pct" not in col:
            filtered_data = data[data[col] > 0]

        mean = get_from_value_map(col, "mean")

        if mean is None:
            mean = filtered_data[col].mean()
            save_to_value_map(col, "mean", mean)

        std_dev = get_from_value_map(col, "std_dev")

        if std_dev is None:
            std_dev = filtered_data[col].std()
            save_to_value_map(col, "std_dev", std_dev)


        z_score = (value - mean) / std_dev
        percentile = (filtered_data[filtered_data[col] < value].shape[0] / filtered_data.shape[0]) * 100
        
        total_z_score += abs(z_score)
        # z_scores.append(f"{z_score:.2f}")
        # percentiles.append(f"{percentile:.2f}%")

    # Calculate maximum width for alignment
    # max_col_width = max([len(col) for col in cols])

    # Display the output
    # print("Columns:    --", "\t".join([col.ljust(max_col_width) for col in cols]))
    # print("Values:     --", "\t".join([value.ljust(max_col_width) for value in values]))
    # print("Z-Scores:   --", "\t".join([z.ljust(max_col_width) for z in z_scores]))
    # print("Percentile: --", "\t".join([p.ljust(max_col_width) for p in percentiles]))
    # print("------------------------------------------------------------------")
    # print(f"Total Z-Score: {total_z_score:.2f}")

    return total_z_score



symbols =[
    "APTUSDT",
    "ASTRUSDT",
    "BALUSDT",
    "BNBUSDT",
    "C98USDT",
    "CELOUSDT",
    "CHZUSDT",
    "CRVUSDT",
    "DOGEUSDT",
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


for symbol in symbols:


    date = "2023-08"

    trading_data = RetriveDataset(symbol, date)
    data = trading_data.retrieve_trading_dataset()

    signals = data[data['news_signal'].isin([-1, 1])].index

    trade_z_scores = []
    print("=====================================================================================================")
    print(f"> News signal: {len(signals)}")

    for news_signal in signals:


        news_signal_minus_5 = news_signal - pd.Timedelta(seconds=5)

        time_range = pd.date_range(start=news_signal_minus_5, periods=11, freq='S')
        index = -5
        news_dict = {
            "time_of_news": str(news_signal),
            "price_at_news": data.loc[news_signal, "avg_price"],
        }

        should_plot_data = False

        # Loop over each timestamp and evaluate the row
        for timestamp in time_range:

            row = data.loc[timestamp]
            total_zscore = row["total_z_score"]
            if total_zscore > 100:
                should_plot_data = True

            news_dict["z_score_" + str(index)] = round(total_zscore, 4)

            index += 1
    
        if should_plot_data:
            news_df = data.loc[timestamp - pd.Timedelta(minutes=10):timestamp + pd.Timedelta(minutes=10)]
            plot_data.plot_data(news_df, symbol, date, "zscore", timestamp) 

        trade_z_scores.append(news_dict)


    os.makedirs(f"local/zscore/{symbol}", exist_ok=True)

    with open(f"local/zscore/{symbol}/trade_z_scores_{date}.json", "w") as f:
        json.dump(trade_z_scores, f, indent=4)


# print(f"Post news row: {post_news_row.name}")
# evaluate_row(post_news_row)


# for i in range(10):
#     print("\n")
#     random_index = random.randint(0, len(data) - 1)

#     random_row = data.iloc[random_index]
#     print(f"Random row: {random_row.name}")
#     evaluate_row(random_row)