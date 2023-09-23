import os
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
import io
from agg_trades_downloader import retrieve_agg_trades
from retrieve_news import GetCryptoNews

load_dotenv()


CONTAINER_NAME = "binancedata"
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
BLOB_SERVICE_CLIENT = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
ACCOUNT_KEY = os.environ['AZURE_STORAGE_ACCOUNT_KEY']
ACCOUNT_URL = os.environ['AZURE_STORAGE_ACCOUNT_URL']


class RetriveDataset():

    def __init__(self, symbol, date, recompile=False, signal_window=None, signal_threshold=None, load_source="local"):
        print("=== RetriveDataset ===")
        print("> Initializing RetriveDataset...")
        print(f"> Symbol: {symbol}")
        print(f"> Date: {date}")

        self.aggregation_window = '1S'
        self.recompile = recompile
        self.signal_window = signal_window
        self.signal_threshold = signal_threshold

        self.data_type = "aggTrades"
        self.symbol = symbol
        self.date = date
        self.interval = "monthly"
        self.load_source = load_source
        self.reduced_trades_filepath = f"reduced_trades/{self.interval}/{symbol}/{symbol}-reduced-{self.aggregation_window}-{self.data_type}-{date}.csv"
        self.agg_trades_filepath = f"aggTrades/{self.interval}/{symbol}/{symbol}-aggTrades-{date}.csv"
        self.local_trading_dataset_filepath = f"local/data/{self.symbol}/trading_dataset_{self.date}.csv"
        self.trading_dataset_filepath = f"trading_datasets/{self.symbol}/trading_dataset_{self.date}.csv"
        self.indicator_dict = {
            "pct_change": {
                "window" : [5, 10, 20, 60]
            }
        }
    
    
    def retrieve_trading_dataset(self):
        
        trading_dataset_df = self.__retrieve_from_blob(self.trading_dataset_filepath, retrieve_type="trading dataset")

        if trading_dataset_df is None or self.recompile:
            reduced_trades_df = self.retrieve_reduced_trades()
            trading_dataset_df = self.add_indicators(reduced_trades_df)
            trading_dataset_df = self.add_news_signals(trading_dataset_df)

            if trading_dataset_df["news_signal"].sum() > 0:
                trading_dataset_df = self.add_total_zscore(trading_dataset_df)
            else:
                trading_dataset_df["total_z_score"] = 0

            trading_dataset_df = self.add_signal(trading_dataset_df)

            self.__save_to_blob(trading_dataset_df, self.trading_dataset_filepath)

        # Replace NaN or Inf with 0
        trading_dataset_df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)

        return trading_dataset_df


    def retrieve_reduced_trades(self):
        print("> Retrieving reduced trades...")
        reduced_trades_df = self.__retrieve_from_blob(self.reduced_trades_filepath, retrieve_type="reduced trades")

        if reduced_trades_df is None:
            print("> Could not retrieve reduced trades from blob")
            reduced_trades_df = self.__build_reduced_trades()
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


    def add_signal(self, df):
        # Create a rolling window for news_signal
        df['temp_rolling_news'] = df['news_signal'].rolling(window=5).max().fillna(0)
        
        # Shift the avg_price
        df['temp_shifted_avg_price'] = df['avg_price'].shift(periods=5, fill_value=df['avg_price'].iloc[0])
        
        # Define the conditions
        zscore_condition = df['total_z_score'] > 100
        news_signal_condition = df['temp_rolling_news'] == 1
        avg_price_increase = df['avg_price'] > df['temp_shifted_avg_price']
        avg_price_decrease = df['avg_price'] < df['temp_shifted_avg_price']

        # Assign signals based on conditions
        df.loc[zscore_condition & news_signal_condition & avg_price_increase, 'signal'] = 1
        df.loc[zscore_condition & news_signal_condition & avg_price_decrease, 'signal'] = -1
        df['signal'].fillna(0, inplace=True)  # Fill NaN values with 0

        # Drop temporary columns
        df.drop(columns=['temp_rolling_news', 'temp_shifted_avg_price'], inplace=True)
        
        return df



    def add_total_zscore(self, df):
        print("> Adding total z-score...")
        # Columns to be considered for z-score calculation
        cols_to_consider = [col for col in df.columns if col not in ["avg_price", "index", "news_signal", "signal"]]
        
        # If "pct" not in column name, filter out rows where the value is 0. Otherwise, use original df.
        valid_data = {col: df[df[col] > 0] if "pct" not in col else df for col in cols_to_consider}
        
        # Compute means and standard deviations
        means = {col: valid_data[col][col].mean() for col in cols_to_consider}
        std_devs = {col: valid_data[col][col].std() for col in cols_to_consider}
        
        # Compute z-scores for entire columns in one go (vectorized)
        z_scores = {col: (df[col] - means[col]) / std_devs[col] for col in cols_to_consider}
        
        # Aggregate z-scores (this will sum across columns for each row)
        df['total_z_score'] = pd.DataFrame(z_scores).abs().sum(axis=1)

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







# SYMBOLS = [ 'LRCUSDT','BTCUSDT','ZECUSDT','EOSUSDT','SOLUSDT','XEMUSDT','OPUSDT','SNXUSDT','1INCHUSDT','TRXUSDT','QTUMUSDT','AGIXUSDT','RUNEUSDT','FLOWUSDT','BNBUSDT','HFTUSDT','APTUSDT','ANKRUSDT','DOGEUSDT','ASTRUSDT','RDNTUSDT','STXUSDT','CTKUSDT','ETHUSDT','NEARUSDT','TUSDT','IOTXUSDT','GRTUSDT','UNIUSDT','ZRXUSDT','DYDXUSDT','ICPUSDT','NEOUSDT','BNXUSDT','SANDUSDT','EGLDUSDT','SSVUSDT','GTCUSDT','MASKUSDT','AMBUSDT','DARUSDT','CELOUSDT','AAVEUSDT','HBARUSDT','ARBUSDT','SXPUSDT','ANTUSDT','ZENUSDT','ICXUSDT','XTZUSDT','YFIUSDT','RSRUSDT','PEOPLEUSDT','DGBUSDT','LINKUSDT','GALUSDT','FTMUSDT','FXSUSDT','TLMUSDT','CELRUSDT','SUSHIUSDT','ALPHAUSDT','ARPAUSDT','HOOKUSDT','MINAUSDT','COTIUSDT','JOEUSDT','ENSUSDT','WOOUSDT','INJUSDT','SKLUSDT','USDCUSDT','IMXUSDT','SFPUSDT','DASHUSDT','MAGICUSDT','PERPUSDT','CTSIUSDT','CHZUSDT','QNTUSDT','LEVERUSDT','IOTAUSDT','IOSTUSDT','WAVESUSDT','TOMOUSDT','BLZUSDT','C98USDT','VETUSDT','ZILUSDT','GMTUSDT','DOTUSDT','ROSEUSDT','LDOUSDT','XLMUSDT','CFXUSDT','LITUSDT','XVSUSDT','OCEANUSDT','BANDUSDT','HOTUSDT','LTCUSDT','AVAXUSDT','ENJUSDT','GALAUSDT','BATUSDT','FETUSDT','BALUSDT','FILUSDT','KAVAUSDT','RNDRUSDT','LPTUSDT','AUDIOUSDT','ALGOUSDT','XRPUSDT','OGNUSDT','GMXUSDT','ACHUSDT','ONTUSDT','KLAYUSDT','REEFUSDT','AXSUSDT','HIGHUSDT','LINAUSDT','ALICEUSDT','DUSKUSDT','FLMUSDT','PHBUSDT','ATOMUSDT','MATICUSDT','LQTYUSDT','STORJUSDT','CKBUSDT','KNCUSDT','MKRUSDT','APEUSDT','API3USDT','NKNUSDT','RVNUSDT','CHRUSDT','MANAUSDT','CRVUSDT','STMXUSDT','ADAUSDT','ATAUSDT','STGUSDT','ARUSDT','IDUSDT','RLCUSDT','THETAUSDT','BLURUSDT','ONEUSDT','TRUUSDT','TRBUSDT','COMPUSDT','IDEXUSDT','SUIUSDT','EDUUSDT','MTLUSDT','1000PEPEUSDT','1000FLOKIUSDT','DENTUSDT','BCHUSDT','1000XECUSDT','JASMYUSDT','UMAUSDT','BELUSDT','1000SHIBUSDT','RADUSDT','XMRUSDT','1000LUNCUSDT','SPELLUSDT','KEYUSDT','COMBOUSDT','UNFIUSDT','CVXUSDT','ETCUSDT','MAVUSDT','MDTUSDT','XVGUSDT','NMRUSDT','BAKEUSDT','WLDUSDT','PENDLEUSDT','ARKMUSDT','AGLDUSDT','YGGUSDT','SEIUSDT' ]



