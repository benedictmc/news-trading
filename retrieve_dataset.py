import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import ResourceNotFoundError
import io
from agg_trades_downloader import retrieve_agg_trades

load_dotenv()


CONTAINER_NAME = "binancedata"
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
BLOB_SERVICE_CLIENT = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
ACCOUNT_KEY = os.environ['AZURE_STORAGE_ACCOUNT_KEY']
ACCOUNT_URL = os.environ['AZURE_STORAGE_ACCOUNT_URL']


class RetriveDataset():

    def __init__(self, symbol, date, signal_window, signal_threshold, load_source="local"):

        self.aggregation_window = '1S'
        self.signal_window = signal_window
        self.signal_threshold = signal_threshold

        self.data_type = "aggTrades"
        self.symbol = symbol
        self.date = date
        self.interval = "monthly"
        self.load_source = load_source
        self.reduced_trades_filepath = f"reduced_trades/{self.interval}/{symbol}/{symbol}-reduced-{self.aggregation_window}-{self.data_type}-{date}.csv"
        self.agg_trades_filepath = f"aggTrades/{self.interval}/{symbol}/{symbol}-aggTrades-{date}.csv"
        self.local_trading_dataset_filepath = f"local/data/{self.symbol}/trading_dataset_{self.date}_sw_{self.signal_window}_st_{str(self.signal_threshold).replace('0.', '')}.csv"
        self.trading_dataset_filepath = f"trading_datasets/{self.symbol}/trading_dataset_{self.date}_sw_{self.signal_window}_st_{str(self.signal_threshold).replace('0.', '')}.csv"
        self.indicator_dict = {
            "pct_change": {
                "window" : [5, 10, 20, 60]
            }
        }
    
    
    def retrieve_trading_dataset(self):
        
        trading_dataset_df = self.__retrieve_from_blob(self.trading_dataset_filepath)

        if trading_dataset_df is None:
            reduced_trades_df = self.retrieve_reduced_trades()
            trading_dataset_df = self.add_indicators(reduced_trades_df)
            trading_dataset_df = self.add_signal(reduced_trades_df)

            self.__save_to_blob(trading_dataset_df, self.trading_dataset_filepath)

        trading_dataset_df.reset_index(inplace=True)

        return trading_dataset_df


    def retrieve_reduced_trades(self):
        reduced_trades_df = self.__retrieve_from_blob(self.reduced_trades_filepath)

        if reduced_trades_df is None:
            print("Could not retrieve reduced trades from blob")
            print("Building reduced trades...")
            reduced_trades_df = self.__build_reduced_trades()
            self.__save_to_blob(reduced_trades_df, self.reduced_trades_filepath)

        else:
            print(f"Retrieved reduced trades from blob for {self.symbol}-{self.date}")

        return reduced_trades_df
    

    def __build_reduced_trades(self):

        agg_trades_df = self.get_agg_trades()

        if agg_trades_df is None:
            print("Could not build reduced trades. Agg trades is does not exist")
            return None
        
        reduced_trades_df = self.__reduce_trades(agg_trades_df)

        if reduced_trades_df is None:
            print("Could not build reduced trades")
            return None

        return reduced_trades_df


    def __save_to_blob(self, df, filepath, local=False):
        print("Saving to blob...")

        csv_data = io.StringIO()
        df.to_csv(csv_data)  # Set index to True if you want to include the DataFrame's index in the CSV
        csv_data.seek(0)

        blob_client = BLOB_SERVICE_CLIENT.get_blob_client(container=CONTAINER_NAME, blob=filepath)
        blob_client.upload_blob(csv_data.getvalue(), overwrite=True)  # Set overwrite to True if you want to replace an existing blob


    def get_agg_trades(self):
        
        agg_trades_df = self.__retrieve_from_blob(self.agg_trades_filepath)

        if agg_trades_df is None:
            retrieve_agg_trades(self.symbol, self.date, self.interval)
            agg_trades_df = self.__retrieve_from_blob(self.agg_trades_filepath)

        return agg_trades_df


    def add_indicators(self, df):

        for indicator, params in self.indicator_dict.items():
            if indicator == "pct_change":
                if self.signal_window not in params['window']:
                    params['window'].append(self.signal_window)
                    params['window'] = sorted(params['window'])

                for window in params['window']:
                    df[f"{indicator}_{window}"] = round(df['avg_price'].pct_change(periods=window), 4)
        
        return df
    

    def add_signal(self, df):
        df['signal'] = 0  # Initialize with 0
        df.loc[df[f'pct_change_{self.signal_window}'] > self.signal_threshold, 'signal'] = 1
        df.loc[df[f'pct_change_{self.signal_window}'] < -1*self.signal_threshold, 'signal'] = -1
    
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

   
    def __retrieve_from_blob(self, blob_file_path):
        try:
            retrieve_file = BLOB_SERVICE_CLIENT.get_blob_client(container=CONTAINER_NAME, blob=blob_file_path)    
                    
            # Download the blob content
            blob_data = retrieve_file.download_blob()
            data = blob_data.readall()
            df = pd.read_csv(io.BytesIO(data), index_col=0)
            return df
        
        except ResourceNotFoundError:
            return None



# SYMBOLS = [ 'LRCUSDT','BTCUSDT','ZECUSDT','EOSUSDT','SOLUSDT','XEMUSDT','OPUSDT','SNXUSDT','1INCHUSDT','TRXUSDT','QTUMUSDT','AGIXUSDT','RUNEUSDT','FLOWUSDT','BNBUSDT','HFTUSDT','APTUSDT','ANKRUSDT','DOGEUSDT','ASTRUSDT','RDNTUSDT','STXUSDT','CTKUSDT','ETHUSDT','NEARUSDT','TUSDT','IOTXUSDT','GRTUSDT','UNIUSDT','ZRXUSDT','DYDXUSDT','ICPUSDT','NEOUSDT','BNXUSDT','SANDUSDT','EGLDUSDT','SSVUSDT','GTCUSDT','MASKUSDT','AMBUSDT','DARUSDT','CELOUSDT','AAVEUSDT','HBARUSDT','ARBUSDT','SXPUSDT','ANTUSDT','ZENUSDT','ICXUSDT','XTZUSDT','YFIUSDT','RSRUSDT','PEOPLEUSDT','DGBUSDT','LINKUSDT','GALUSDT','FTMUSDT','FXSUSDT','TLMUSDT','CELRUSDT','SUSHIUSDT','ALPHAUSDT','ARPAUSDT','HOOKUSDT','MINAUSDT','COTIUSDT','JOEUSDT','ENSUSDT','WOOUSDT','INJUSDT','SKLUSDT','USDCUSDT','IMXUSDT','SFPUSDT','DASHUSDT','MAGICUSDT','PERPUSDT','CTSIUSDT','CHZUSDT','QNTUSDT','LEVERUSDT','IOTAUSDT','IOSTUSDT','WAVESUSDT','TOMOUSDT','BLZUSDT','C98USDT','VETUSDT','ZILUSDT','GMTUSDT','DOTUSDT','ROSEUSDT','LDOUSDT','XLMUSDT','CFXUSDT','LITUSDT','XVSUSDT','OCEANUSDT','BANDUSDT','HOTUSDT','LTCUSDT','AVAXUSDT','ENJUSDT','GALAUSDT','BATUSDT','FETUSDT','BALUSDT','FILUSDT','KAVAUSDT','RNDRUSDT','LPTUSDT','AUDIOUSDT','ALGOUSDT','XRPUSDT','OGNUSDT','GMXUSDT','ACHUSDT','ONTUSDT','KLAYUSDT','REEFUSDT','AXSUSDT','HIGHUSDT','LINAUSDT','ALICEUSDT','DUSKUSDT','FLMUSDT','PHBUSDT','ATOMUSDT','MATICUSDT','LQTYUSDT','STORJUSDT','CKBUSDT','KNCUSDT','MKRUSDT','APEUSDT','API3USDT','NKNUSDT','RVNUSDT','CHRUSDT','MANAUSDT','CRVUSDT','STMXUSDT','ADAUSDT','ATAUSDT','STGUSDT','ARUSDT','IDUSDT','RLCUSDT','THETAUSDT','BLURUSDT','ONEUSDT','TRUUSDT','TRBUSDT','COMPUSDT','IDEXUSDT','SUIUSDT','EDUUSDT','MTLUSDT','1000PEPEUSDT','1000FLOKIUSDT','DENTUSDT','BCHUSDT','1000XECUSDT','JASMYUSDT','UMAUSDT','BELUSDT','1000SHIBUSDT','RADUSDT','XMRUSDT','1000LUNCUSDT','SPELLUSDT','KEYUSDT','COMBOUSDT','UNFIUSDT','CVXUSDT','ETCUSDT','MAVUSDT','MDTUSDT','XVGUSDT','NMRUSDT','BAKEUSDT','WLDUSDT','PENDLEUSDT','ARKMUSDT','AGLDUSDT','YGGUSDT','SEIUSDT' ]



