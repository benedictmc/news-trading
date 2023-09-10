from retrieve_dataset import TradingSimulator
import pandas as pd
import matplotlib.pyplot as plt

symbol = "BTCUSDT"
date = "2023-08"

trading_simulator = TradingSimulator(symbol, date, load_source="blob")
trading_simulator.build_reduced_trades()
df = trading_simulator.reduced_trades_df
df.reset_index(inplace=True)


def percentage_change(old, new):
    """Calculate the percentage change between two numbers."""
    return ((new - old) / old) * 100


def isolate_spikes(df, change_column, cool_down_seconds=600, top_n=100):
    """
    Isolate significant price changes (spikes) from a DataFrame.

    Parameters:
    - df (pd.DataFrame): The input DataFrame. Must have datetime as index.
    - change_column (str): Name of the column containing percentage changes.
    - cool_down_seconds (int): Number of seconds to wait before detecting another spike.
    - top_n (int): Number of top isolated spikes to return.

    Returns:
    - pd.DataFrame: DataFrame containing the isolated spikes.
    """
    
    # Sort data by absolute change
    sorted_df = df.sort_values(by=change_column, key=abs, ascending=False)
    
    # To store rows corresponding to the initial moments of the spikes
    spike_rows = []

    # Track the last detected spike timestamp
    last_detected_spike = None

    for index, row in sorted_df.iterrows():
        if last_detected_spike is None or (index - last_detected_spike > pd.Timedelta(seconds=cool_down_seconds)):
            spike_rows.append(row)
            last_detected_spike = index

            # Break once we've detected the desired number of spikes
            if len(spike_rows) == top_n:
                break

    # Convert spike_rows list to a DataFrame
    spike_df = pd.DataFrame(spike_rows)

    return spike_df



# Convert 'flooored_time' column to datetime format
df['flooored_time'] = pd.to_datetime(df['flooored_time'])

# Set 'flooored_time' as the index
df.set_index('flooored_time', inplace=True)

# Resample at 1 second frequency and forward fill the 'avg_price' column
df_resampled = df.resample('1S').first()
df_resampled['avg_price'] = df_resampled['avg_price'].ffill()

# Add a column that calculates the percentage change in price every 10 minutes
df_resampled['percentage_change_20sec'] = percentage_change(df_resampled['avg_price'].shift(20), df_resampled['avg_price'])

df_resampled['price_minus_20sec'] = df_resampled['avg_price'].shift(20)

# Compute the absolute value of 'percentage_change_20sec'
# df_resampled['abs_percentage_change_20sec'] = df_resampled['percentage_change_20sec'].abs()

df_resampled.to_csv("df_resampled.csv")







# spikes = []
# lookahead_window_seconds = 600
# threshold = 0.5  # 3%
# time_diffs = df['flooored_time'].diff().dropna().unique()
# # The smallest time difference in the dataset (in seconds)
# min_time_diff_seconds = pd.Timedelta(min(time_diffs)).seconds

# # Calculate the rolling window size
# rolling_window_size = lookahead_window_seconds // min_time_diff_seconds

# # Calculate rolling max and min prices
# df['rolling_max_forward'] = df['avg_price'].iloc[::-1].rolling(window=rolling_window_size, min_periods=1).max().iloc[::-1]
# df['rolling_min_forward'] = df['avg_price'].iloc[::-1].rolling(window=rolling_window_size, min_periods=1).min().iloc[::-1]

# # Calculate percentage changes for the forward-looking rolling max and min compared to the current price
# df['max_change_forward'] = percentage_change(df['avg_price'], df['rolling_max_forward'])
# df['min_change_forward'] = percentage_change(df['avg_price'], df['rolling_min_forward'])

# # Display a subset of the DataFrame for inspection
# df_debug_forward = df[['flooored_time', 'avg_price', 'rolling_max_forward', 'rolling_min_forward', 'max_change_forward', 'min_change_forward']]
# df_debug_forward[(df_debug_forward['max_change_forward'].abs() >= threshold) | (df_debug_forward['min_change_forward'].abs() >= threshold)]
# # Filter rows where either max_change or min_change meets or exceeds the threshold
# spike_df = df[(df['max_change'].abs() >= threshold) | (df['min_change'].abs() >= threshold)]

# # Extract relevant information
# spikes_improved = []
# for _, row in spike_df.iterrows():
#     change = row['max_change'] if abs(row['max_change']) > abs(row['min_change']) else row['min_change']
#     spikes_improved.append({
#         'start_time': row['flooored_time'] - pd.Timedelta(seconds=lookahead_window_seconds),
#         'end_time': row['flooored_time'],
#         'percentage_change': change
#     })
# print(spikes)