import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import ResourceNotFoundError
import io

load_dotenv()

NEWS_API_ENDPOINT = "https://news.treeofalpha.com/api"
CONTAINER_NAME = "binancedata"
BLOB_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
BLOB_SERVICE_CLIENT = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
ACCOUNT_KEY = os.environ['AZURE_STORAGE_ACCOUNT_KEY']
ACCOUNT_URL = os.environ['AZURE_STORAGE_ACCOUNT_URL']


class TradingSimulator():

    def __init__(self, symbol, date, load_source="local"):
        # self.news = self.get_all_news()
        # self.news_start_time = 1682100506000
        # self.news_end_time = int(time.time()*1000)
        # self.news_second_dict = self.create_news_time_dict(self.get_all_news())
        # self.live_news = {}
        # self.expiry_dict = {}
        self.aggregation_window = '1S'
        self.data_type = "aggTrades"
        self.symbol = symbol
        self.date = date
        self.interval = "monthly"
        self.load_source = load_source
        self.reduced_trades_filepath = f"reduced_trades/{self.interval}/{symbol}/{symbol}-reduced-{self.aggregation_window}-{self.data_type}-{date}.csv"
        self.agg_trades_filepath = f"aggTrades/{self.interval}/{symbol}/{symbol}-aggTrades-{date}.csv"
        

    # -------------
    # News methods (Not used yet)
    # -------------
    def create_news_time_dict(self, news_list):
        # Create a dictionary with the trimmed (to seconds) news article time as the key
        news_dict = {}
        for news in news_list:
            news_second = (news['time'] // 1000) * 1000
            if news_second not in news_dict:
                news_dict[news_second] = [news]
            else:
                news_dict[news_second].append(news)

        return news_dict

        return set([(news['time'] // 1000) * 1000 for news in news_list])


    def get_all_news(self, limit=500):

        if os.path.exists("data/news/all_news.json"):
            with open("data/news/all_news.json", "r") as f:
                return json.load(f)
        else:
            url =  f"{NEWS_API_ENDPOINT}/allNews"
            response = requests.get(url)
            return response.json()
    

    def handle_live_news(self, second):

        if len(self.live_news) == 0:
            return
        
        for news_id, news_item in self.live_news.items():
            nearest_minute = (second // 60000) * 60000

            if news_item["last_updated"] == nearest_minute:
                continue

            nearest_minute_pd = pd.Timestamp(nearest_minute, unit='ms')
            ohlc = fetch_data(news_item["symbol"], "1m", nearest_minute_pd, nearest_minute_pd)
            lastest_price = ohlc['open'].iloc[0]
            news_price = news_item["price_news_open"]
            change = round((lastest_price - news_price) / news_price, 4)
            news_item["price_change"] = change
            news_item["last_updated"] = nearest_minute


            if abs(change) > 0.01:
                print(f">> Updated news item at {second} : ", news_item)
                print("Major change: ", news_item)

              
    def interate_time(self):

        for second in range(self.news_start_time, self.news_end_time, 1000):
            pd_second = pd.Timestamp(second, unit='ms')

            if second in self.news_second_dict:
                expiry_time = second + (60*1000*10)
                

                
                for news in self.news_second_dict[second]:
                    news_id = news["_id"]
                    binance_symbols = get_binance_symbols(news["suggestions"])
                    symbol = None


                    if len(binance_symbols) != 0:
                        symbol = binance_symbols[0] # Just take the first one for now
                    
                    if symbol is None:
                        continue
                    
                    # Get nearest minute to second
                    nearest_minute = (second // 60000) * 60000
                    # Nearst minute to pd timestamp
                    nearest_minute_pd = pd.Timestamp(nearest_minute, unit='ms')

                    ohlc = fetch_data(symbol, "1m", nearest_minute_pd, nearest_minute_pd)

                    # Adds to the expiry dict
                    if expiry_time not in self.expiry_dict:
                        self.expiry_dict[expiry_time] = [news_id]
                    else:
                        self.expiry_dict[expiry_time].append(news_id)

                    # Adds to the live news dict
                    self.live_news[news_id] = {
                        "news": news["title"],
                        "id": news_id,
                        "second_added": second,
                        "minute_added": nearest_minute,
                        "price_news_open": ohlc['open'].iloc[0],
                        "price_news_close": ohlc['close'].iloc[0],
                        "symbol": symbol,
                        "expiry_time": expiry_time, 
                        "last_updated": nearest_minute,
                    }

            if second in self.expiry_dict:
                for news_id in self.expiry_dict[second]:
                    del self.live_news[news_id]

                del self.expiry_dict[second]

            self.handle_live_news(second)

    # -------------
    # News methods End (Not used yet)
    # -------------

    def build_reduced_trades(self):

        self.reduced_trades_df = self.get_reduced_trades()   

        if self.reduced_trades_df is None:
            print("Could not build reduced trades")
            return
        
        
    def save_reduced_trades(self, reduced_trades_df):
        csv_data = io.StringIO()
        reduced_trades_df.to_csv(csv_data, index=False)  # Set index to True if you want to include the DataFrame's index in the CSV
        csv_data.seek(0)
        
        blob_client = BLOB_SERVICE_CLIENT.get_blob_client(container=CONTAINER_NAME, blob=self.reduced_trades_filepath)
        blob_client.upload_blob(csv_data.getvalue(), overwrite=True)  # Set overwrite to True if you want to replace an existing blob


    def get_reduced_trades(self):
        
        reduced_trades_df = self.__retrieve_from_blob(self.reduced_trades_filepath)

        if reduced_trades_df is None:

            agg_trades_df = self.__retrieve_from_blob(self.agg_trades_filepath)
            reduced_trades_df = self.__reduce_trades(agg_trades_df)

            if reduced_trades_df is None:
                return None
            
            self.save_reduced_trades(reduced_trades_df)

            reduced_trades_df.index = reduced_trades_df['flooored_time']
            reduced_trades_df = reduced_trades_df.drop(columns=['flooored_time'])

        else:
            print(f"Retrieved reduced trades from blob for {self.symbol}-{self.date}")

        return reduced_trades_df
        
        
    def __reduce_trades(self, agg_trades_df):

        if agg_trades_df is None:
            print("No trades to reduce")
            return None

        # Check if 'transact_time' is not already a datetime object
        if not isinstance(agg_trades_df['transact_time'].iloc[0], pd.Timestamp):
            # Convert transact_time to datetime
            agg_trades_df['transact_time'] = pd.to_datetime(agg_trades_df['transact_time'], unit='ms')

        # Round transact_time to the nearest second
        agg_trades_df['flooored_time'] = agg_trades_df['transact_time'].dt.floor(self.aggregation_window)

        # Calculate the number of trades for each row
        agg_trades_df['num_trades'] = agg_trades_df['last_trade_id'] - agg_trades_df['first_trade_id'] + 1

        # Compute average price for all transactions
        overall_avg_price = agg_trades_df.groupby('flooored_time')['price'].mean()

        # Split dataframe for buys and sells
        buys = agg_trades_df[agg_trades_df['is_buyer_maker']]
        sells = agg_trades_df[~agg_trades_df['is_buyer_maker']]

        # Reduce separately for buy and sell
        buy_agg = buys.groupby('flooored_time').agg(
            sum_asset_bought=('quantity', 'sum'),
            num_of_trades_bought=('num_trades', 'sum')
        )

        sell_agg = sells.groupby('flooored_time').agg(
            sum_asset_sold=('quantity', 'sum'),
            num_of_trades_sold=('num_trades', 'sum')
        )

        # Merge on the flooored_time
        agg_df = pd.merge(overall_avg_price, buy_agg, on='flooored_time', how='outer')
        agg_df = pd.merge(agg_df, sell_agg, on='flooored_time', how='outer').reset_index()

        # Round off float columns to desired precision
        precision = 2  # Change this as per your requirement
        agg_df = agg_df.round({'sum_asset_bought': precision, 'sum_asset_sold': precision})
        agg_df = agg_df.round({'price': 6})

        # Rename the price column to avg_price
        agg_df.rename(columns={'price': 'avg_price'}, inplace=True)

        # agg_df.index = agg_df['flooored_time']
        # agg_df = agg_df.drop(columns=['flooored_time'])
        return agg_df


    # def plot_reduced_trades(self, reduced_trades_df):
    #     fig, ax1 = plt.subplots(figsize=(15, 8))

    #     # Line plot for average price
    #     ax1.plot(agg_df['rounded_time'], agg_df['avg_price'], color='b', label='Average Price', linewidth=2)
    #     ax1.set_xlabel('Time')
    #     ax1.set_ylabel('Average Price', color='b')
    #     ax1.tick_params(axis='y', labelcolor='b')

    #     ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    #     width = (agg_df['rounded_time'].iloc[1] - agg_df['rounded_time'].iloc[0]).seconds / (3 * 86400)  # Width of bars based on the time difference between entries

    #     # Bar plots for volumes
    #     ax2.bar(agg_df['rounded_time'], agg_df['sum_asset_bought'], width=width, alpha=0.6, label='Bought Volume', color='g')
    #     ax2.bar(agg_df['rounded_time'], -agg_df['sum_asset_sold'], width=width, alpha=0.6, label='Sold Volume', color='r')
    #     ax2.set_ylabel('Volume', color='g')  # Green for bought volume
    #     ax2.tick_params(axis='y', labelcolor='g')

    #     # Title and show the plot
    #     plt.title('Trade Dynamics Over Time')
    #     fig.tight_layout()  # Otherwise the right y-label is slightly clipped
    #     plt.legend(loc='upper left')
    #     plt.show()

    
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

SYMBOLS = [ 'LRCUSDT','BTCUSDT','ZECUSDT','EOSUSDT','SOLUSDT','XEMUSDT','OPUSDT','SNXUSDT','1INCHUSDT','TRXUSDT','QTUMUSDT','AGIXUSDT','RUNEUSDT','FLOWUSDT','BNBUSDT','HFTUSDT','APTUSDT','ANKRUSDT','DOGEUSDT','ASTRUSDT','RDNTUSDT','STXUSDT','CTKUSDT','ETHUSDT','NEARUSDT','TUSDT','IOTXUSDT','GRTUSDT','UNIUSDT','ZRXUSDT','DYDXUSDT','ICPUSDT','NEOUSDT','BNXUSDT','SANDUSDT','EGLDUSDT','SSVUSDT','GTCUSDT','MASKUSDT','AMBUSDT','DARUSDT','CELOUSDT','AAVEUSDT','HBARUSDT','ARBUSDT','SXPUSDT','ANTUSDT','ZENUSDT','ICXUSDT','XTZUSDT','YFIUSDT','RSRUSDT','PEOPLEUSDT','DGBUSDT','LINKUSDT','GALUSDT','FTMUSDT','FXSUSDT','TLMUSDT','CELRUSDT','SUSHIUSDT','ALPHAUSDT','ARPAUSDT','HOOKUSDT','MINAUSDT','COTIUSDT','JOEUSDT','ENSUSDT','WOOUSDT','INJUSDT','SKLUSDT','USDCUSDT','IMXUSDT','SFPUSDT','DASHUSDT','MAGICUSDT','PERPUSDT','CTSIUSDT','CHZUSDT','QNTUSDT','LEVERUSDT','IOTAUSDT','IOSTUSDT','WAVESUSDT','TOMOUSDT','BLZUSDT','C98USDT','VETUSDT','ZILUSDT','GMTUSDT','DOTUSDT','ROSEUSDT','LDOUSDT','XLMUSDT','CFXUSDT','LITUSDT','XVSUSDT','OCEANUSDT','BANDUSDT','HOTUSDT','LTCUSDT','AVAXUSDT','ENJUSDT','GALAUSDT','BATUSDT','FETUSDT','BALUSDT','FILUSDT','KAVAUSDT','RNDRUSDT','LPTUSDT','AUDIOUSDT','ALGOUSDT','XRPUSDT','OGNUSDT','GMXUSDT','ACHUSDT','ONTUSDT','KLAYUSDT','REEFUSDT','AXSUSDT','HIGHUSDT','LINAUSDT','ALICEUSDT','DUSKUSDT','FLMUSDT','PHBUSDT','ATOMUSDT','MATICUSDT','LQTYUSDT','STORJUSDT','CKBUSDT','KNCUSDT','MKRUSDT','APEUSDT','API3USDT','NKNUSDT','RVNUSDT','CHRUSDT','MANAUSDT','CRVUSDT','STMXUSDT','ADAUSDT','ATAUSDT','STGUSDT','ARUSDT','IDUSDT','RLCUSDT','THETAUSDT','BLURUSDT','ONEUSDT','TRUUSDT','TRBUSDT','COMPUSDT','IDEXUSDT','SUIUSDT','EDUUSDT','MTLUSDT','1000PEPEUSDT','1000FLOKIUSDT','DENTUSDT','BCHUSDT','1000XECUSDT','JASMYUSDT','UMAUSDT','BELUSDT','1000SHIBUSDT','RADUSDT','XMRUSDT','1000LUNCUSDT','SPELLUSDT','KEYUSDT','COMBOUSDT','UNFIUSDT','CVXUSDT','ETCUSDT','MAVUSDT','MDTUSDT','XVGUSDT','NMRUSDT','BAKEUSDT','WLDUSDT','PENDLEUSDT','ARKMUSDT','AGLDUSDT','YGGUSDT','SEIUSDT' ]
date = "2023-07"


for symbol in SYMBOLS:
    trading_simulator = TradingSimulator(symbol, date, load_source="blob")
    trading_simulator.build_reduced_trades()
    print(f"Symbol: {symbol} - Date: {date}")
    print("RESULT:")
    print(trading_simulator.reduced_trades_df.head())

