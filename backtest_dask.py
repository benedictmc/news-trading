import dask.dataframe as dd
from dask.distributed import Client

def process_data():
    # Load the data into a Dask DataFrame
    df = dd.read_csv('data/aggregate/BTCUSDT-reduced-aggTrades-2023-08.csv', parse_dates=['rounded_time'])

    def apply_strategy(partition_df):
        # Calculate rolling averages for 10 and 50 seconds
        partition_df['short_avg'] = partition_df['avg_price'].rolling(window=10).mean()
        partition_df['long_avg'] = partition_df['avg_price'].rolling(window=50).mean()

        # Create buy/sell signals
        partition_df['signal'] = (partition_df['short_avg'] > partition_df['long_avg']).astype(int)
        partition_df['signal'] = partition_df['signal'].shift().fillna(0)  # Shift to avoid lookahead bias

        # (Optional) Calculate returns or other metrics here...

        return partition_df

    # Apply the strategy function to each partition of the Dask DataFrame
    result_df = df.map_partitions(apply_strategy)

    # Gather the results to a Pandas DataFrame
    final_result = result_df.compute()
    print(final_result.head())


if __name__ == '__main__':
    client = Client(n_workers=4)  # Optionally specify parameters, e.g., Client(n_workers=4)
    process_data()
    client.close()