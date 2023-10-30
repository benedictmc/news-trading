import os
import pandas as pd
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
import io
from retrieve_binance.agg_trades_downloader import retrieve_agg_trades
from retrieve_binance.retrieve_news import GetCryptoNews
import numpy as np


load_dotenv()


CONTAINER_NAME = "binancedata"
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
BLOB_SERVICE_CLIENT = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
ACCOUNT_KEY = os.environ['AZURE_STORAGE_ACCOUNT_KEY']
ACCOUNT_URL = os.environ['AZURE_STORAGE_ACCOUNT_URL']


# Example config
# {
#     "columns": [
#         "avg_price",
#         "sum_asset_bought",
#         "num_of_trades_bought",
#         "sum_asset_sold",
#         "num_of_trades_sold",
#     ], 
#     "features": [
#         {
#             "type": "zscore",
#             "columns": [
#                 "sum_asset_bought",
#                 "num_of_trades_bought",
#                 "sum_asset_sold",
#                 "num_of_trades_sold",
#             ]
#         }
#     ], 
#     "signal": {
#         "column": "sum_asset_sold_zscore",
#         "threshold": 100,
#     }
# }


class RetriveDataset():

    def __init__(self, symbol, date, config, recompile=False, load_source="local"):
        print("=== RetriveDataset ===")
        print("> Initializing RetriveDataset...")
        print(f"> Symbol: {symbol}")
        print(f"> Date: {date}")

        self.aggregation_window = '1S'
        self.recompile = recompile
        self.config = config

        self.data_type = "aggTrades"
        self.symbol = symbol
        self.date = date
        self.interval = "monthly"
        self.load_source = load_source
        self.reduced_trades_filepath = f"reduced_trades/{self.interval}/{symbol}/{symbol}-reduced-{self.aggregation_window}-{self.data_type}-{date}.csv"
        self.agg_trades_filepath = f"aggTrades/{self.interval}/{symbol}/{symbol}-aggTrades-{date}.csv"
        self.local_trading_dataset_filepath = f"local/data/{self.symbol}/trading_dataset_{self.date}.csv"
        self.trading_dataset_filepath = f"trading_datasets/{self.symbol}/trading_dataset_{self.date}.csv"
    
    
    def retrieve_trading_dataset(self):
        
        trading_dataset_df = self.__retrieve_from_blob(self.trading_dataset_filepath, retrieve_type="trading dataset")
        
        if trading_dataset_df is None:
            trading_dataset_df = self.retrieve_reduced_trades()
            # Happens when could not build
            if trading_dataset_df is None:
                print("> Could not retrieve reduced trades")
                return None

        if "signal" in trading_dataset_df.columns:      
            trading_dataset_df = trading_dataset_df.drop(columns=['signal'])

        if len(set(self.config["columns"]) - set(trading_dataset_df.columns)) > 0:
            print(f"> Columns {set(self.config['columns']) - set(trading_dataset_df.columns)} missing from trading dataset")
            raise Exception("Columns missing from trading dataset")
        
        needed_columns = self.config["columns"]
        
        added_column = False
        
        if "features" in self.config:
            for feature in self.config["features"]:
                feature_type = feature['type']

                # Add feature types here:
                if feature_type == "zscore":
                    for column in feature["columns"]:
                        dataset_column = f"{column}_{feature_type}"
                        needed_columns.append(dataset_column)
                        # Build new column if doesn't exist 
                        # if dataset_column not in trading_dataset_df.columns:
                        trading_dataset_df = self.add_zscore(column, trading_dataset_df)
                        added_column = True
                
                if feature_type == "news_signal":
                    dataset_column = "news_signal"
                    needed_columns.append(dataset_column)

                    if dataset_column not in trading_dataset_df.columns:
                        trading_dataset_df = self.add_news_signals(trading_dataset_df)
                        added_column = True

                if feature_type == "future_diff":
                    for period in feature["periods"]:
                        for column in feature["columns"]:
                            dataset_column = f"{column}_{feature_type}_{period}"
                            needed_columns.append(dataset_column)

                            if dataset_column not in trading_dataset_df.columns:
                                trading_dataset_df[dataset_column] = -round(trading_dataset_df[column].pct_change(periods=-period), 4)
                                added_column = True
                
                if feature_type == "moving_average":
                    for period in feature["periods"]:
                        for column in feature["columns"]:
                            dataset_column = f"{column}_{feature_type}_MA_{period}"
                            needed_columns.append(dataset_column)
                            # print(dataset_column)
                            # print(trading_dataset_df[column].rolling(period))
                            # print(round(trading_dataset_df[column].fillna(0).rolling(period).mean(), 2))
                            # print(len(trading_dataset_df[column].rolling(period).mean().value_counts()))
                            # exit()
                            # if dataset_column not in trading_dataset_df.columns:
                            trading_dataset_df[dataset_column] = round(trading_dataset_df[column].fillna(0).rolling(period).mean(), 2)
                            added_column = True


            if added_column:
                self.__save_to_blob(trading_dataset_df, self.trading_dataset_filepath)

        if "signal" in self.config:
            trading_dataset_df = self.add_signal(trading_dataset_df, self.config["signal"])
            needed_columns.append("signal")

        trading_dataset_df = trading_dataset_df[needed_columns]
        
        trading_dataset_df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)
        trading_dataset_df.index = pd.to_datetime(trading_dataset_df.index)

        return trading_dataset_df
    

    def retrieve_reduced_trades(self):
        print("> Retrieving reduced trades...")
        reduced_trades_df = self.__retrieve_from_blob(self.reduced_trades_filepath, retrieve_type="reduced trades")

        if reduced_trades_df is None:
            print("> Could not retrieve reduced trades from blob")
            reduced_trades_df = self.__build_reduced_trades()
            if not reduced_trades_df is None:
                self.__save_to_blob(reduced_trades_df, self.reduced_trades_filepath)

        else:
            print(f"> Retrieved reduced trades from blob for {self.symbol}-{self.date}")

        return reduced_trades_df
    

    def __build_reduced_trades(self):
        print("> Building reduced trades...")
        agg_trades_df = self.get_agg_trades()

        if agg_trades_df is None:
            print("> Could not build reduced trades. Agg trades is does not exist")
            return None
        
        reduced_trades_df = self.__reduce_trades(agg_trades_df)

        if reduced_trades_df is None:
            print("> Could not build reduced trades")
            return None

        return reduced_trades_df


    def __save_to_blob(self, df, filepath, local=False):
        print("> Saving to blob...")

        csv_data = io.StringIO()
        df.to_csv(csv_data)  # Set index to True if you want to include the DataFrame's index in the CSV
        csv_data.seek(0)

        blob_client = BLOB_SERVICE_CLIENT.get_blob_client(container=CONTAINER_NAME, blob=filepath)
        blob_client.upload_blob(csv_data.getvalue(), overwrite=True)  # Set overwrite to True if you want to replace an existing blob


    def get_agg_trades(self):
        print("> Retrieving agg trades...")
        agg_trades_df = self.__retrieve_from_blob(self.agg_trades_filepath, "agg trades")

        if agg_trades_df is None:
            print("> Could not retrieve agg trades from blob")
            print("> Retrieving agg trades from binance...")
            retrieve_agg_trades(self.symbol, self.date, self.interval)
            agg_trades_df = self.__retrieve_from_blob(self.agg_trades_filepath, "agg trades")

        return agg_trades_df


    def add_indicators(self, df):

        for indicator, params in self.indicator_dict.items():
            if indicator == "pct_change":

                # Can't remember why I did this
                if self.signal_window and self.signal_window not in params['window']:
                    params['window'].append(self.signal_window)
                    params['window'] = sorted(params['window'])

                for window in params['window']:
                    df[f"{indicator}_{window}"] = round(df['avg_price'].pct_change(periods=window), 4)
        
        return df
    

    def add_news_signals(self, df):
        
        start_time = df.index.values[0]
        end_time = df.index.values[-1]
        
        if not (isinstance(start_time, str) and isinstance(end_time, str)):
            start_time_pd = pd.Timestamp(start_time)
            end_time_pd = pd.Timestamp(end_time)
            start_time = start_time_pd.strftime('%Y-%m-%d %H:%M:%S')
            end_time = end_time_pd.strftime('%Y-%m-%d %H:%M:%S')

        print(f"> Retrieving news from {start_time} to {end_time}...")

        news_class = GetCryptoNews(start_time, end_time, symbol=self.symbol)
        news_class.filter_news()
        news_df = news_class.create_news_df()

        df.index = pd.to_datetime(df.index)
        df = pd.merge(df, news_df, left_index=True, right_index=True, how='outer')

        return df


    def add_signal(self, df, signal_config):
        print("> Adding signal")

        # Weird bug where signal is alerady in df
        if 'signal' in df.columns:
            print("> Signal column already in df")
            df = df.drop(columns=['signal'])

        signal_col = signal_config["column"]
        threshold = signal_config["threshold"]

        if signal_col not in df.columns:
            print("> Error: Signal column not in trading dataset")
            return None
        
        df['signal'] = np.where(
            (df[signal_col] > threshold),
            1, 0
        )
        
        return df


    def add_zscore(self, column, df, window='1H'):
        print(f"> Adding column-wise z-scores for {column}...")

        # Compute means and standard deviations
        # Compute rolling means and standard deviations
        rolling_mean = df[column].fillna(0).rolling(window=window).mean().shift(1)
        rolling_std = df[column].fillna(0).rolling(window=window).std().shift(1)
        
        df[f'{column}_zscore'] = round((df[column] - rolling_mean) / rolling_std, 2)

        return df


    def __reduce_trades(self, agg_trades_df):

        if agg_trades_df is None:
            print("No trades to reduce")
            return None

        # Check if 'transact_time' is not already a datetime object
        if not isinstance(agg_trades_df['transact_time'].iloc[0], pd.Timestamp):
            # Convert transact_time to datetime
            agg_trades_df['transact_time'] = pd.to_datetime(agg_trades_df['transact_time'], unit='ms')

        # Round transact_time to the nearest second
        agg_trades_df['floored_time'] = agg_trades_df['transact_time'].dt.floor(self.aggregation_window)

        # Calculate the number of trades for each row
        agg_trades_df['num_trades'] = agg_trades_df['last_trade_id'] - agg_trades_df['first_trade_id'] + 1

        # Compute average price for all transactions
        overall_avg_price = agg_trades_df.groupby('floored_time')['price'].mean()

        # Split dataframe for buys and sells
        buys = agg_trades_df[agg_trades_df['is_buyer_maker']]
        sells = agg_trades_df[~agg_trades_df['is_buyer_maker']]

        # Reduce separately for buy and sell
        buy_agg = buys.groupby('floored_time').agg(
            sum_asset_bought=('quantity', 'sum'),
            num_of_trades_bought=('num_trades', 'sum')
        )

        sell_agg = sells.groupby('floored_time').agg(
            sum_asset_sold=('quantity', 'sum'),
            num_of_trades_sold=('num_trades', 'sum')
        )

        # Merge on the floored_time
        agg_df = pd.merge(overall_avg_price, buy_agg, on='floored_time', how='outer')
        agg_df = pd.merge(agg_df, sell_agg, on='floored_time', how='outer').reset_index()

        # Round off float columns to desired precision
        precision = 2  # Change this as per your requirement
        agg_df = agg_df.round({'sum_asset_bought': precision, 'sum_asset_sold': precision})
        agg_df = agg_df.round({'price': 6})

        # Rename the price column to avg_price
        agg_df.rename(columns={'price': 'avg_price'}, inplace=True)

        # Set index to floored_time
        agg_df.index = pd.to_datetime(agg_df.floored_time)
        
        # Drop the floored_time column
        agg_df.drop('floored_time', axis=1, inplace=True)

        # Fill forward avg price values
        agg_df = agg_df.resample('1S').first()

        agg_df['avg_price'] = agg_df['avg_price'].ffill()

        return agg_df

   
    def __retrieve_from_blob(self, blob_file_path, retrieve_type=""):
        print(f"> Attempting to retrieve {retrieve_type} from blob...")
        try:
            retrieve_file = BLOB_SERVICE_CLIENT.get_blob_client(container=CONTAINER_NAME, blob=blob_file_path)    
                    
            # Download the blob content
            blob_data = retrieve_file.download_blob()
            data = blob_data.readall()
            # Bit of a hack
            if retrieve_type == "trading dataset":
                df = pd.read_csv(io.BytesIO(data), index_col=0, parse_dates=True)
            else:
                df = pd.read_csv(io.BytesIO(data), index_col=0)
            return df
        
        except ResourceNotFoundError:
            print(f"> {retrieve_type} does not exist in blob")
            return None

