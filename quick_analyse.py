import json
import os

all_shorts = {}

for coin in os.listdir('local/results'):
    for indicator in os.listdir(f'local/results/{coin}'):
        if 'trade_list.json' in os.listdir(f'local/results/{coin}/{indicator}'):
            with open(f'local/results/{coin}/{indicator}/trade_list.json', 'r') as f:
                trades = json.load(f)
            for trade in trades:
                if 'position_type' not in trade:
                    continue

                if trade['position_type'] == 'short':
                    all_shorts[trade['max_neg_pct_change']] = f'local/results/{coin}/{indicator}/trade_list.json'






# Sort keys of dictionary keep track of the order

sorted_dict = dict(sorted(all_shorts.items()))

                
for k, val in sorted_dict.items():
    print(k, val)



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