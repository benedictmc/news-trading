import os
import json
import requests
import pandas as pd
import time
from compile_news import get_binance_symbols
from retrieve_data import fetch_data
import matplotlib.pyplot as plt

NEWS_API_ENDPOINT = "https://news.treeofalpha.com/api"

class TradingSimulator():

    def __init__(self):
        # self.news = self.get_all_news()
        self.news_start_time = 1682100506000
        self.news_end_time = int(time.time()*1000)
        self.trades_df = self.__get_load_trades()

        self.aggregation_window = '1S'

        # self.news_second_dict = self.create_news_time_dict(self.get_all_news())
        # self.live_news = {}
        # self.expiry_dict = {}


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


    def __get_load_trades(self):
        trades_df = pd.read_csv("data/trades/BTCUSDT-aggTrades-2023-08.csv", index_col=0)
        return trades_df
    


    def aggregate_trades(self):
        # Check if 'transact_time' is not already a datetime object
        if not isinstance(self.trades_df['transact_time'].iloc[0], pd.Timestamp):
            # Convert transact_time to datetime
            self.trades_df['transact_time'] = pd.to_datetime(self.trades_df['transact_time'], unit='ms')

        # Round transact_time to the nearest second
        self.trades_df['rounded_time'] = self.trades_df['transact_time'].dt.round(self.aggregation_window)

        # Calculate the number of trades for each row
        self.trades_df['num_trades'] = self.trades_df['last_trade_id'] - self.trades_df['first_trade_id'] + 1

        # Compute average price for all transactions
        overall_avg_price = self.trades_df.groupby('rounded_time')['price'].mean()

        # Split dataframe for buys and sells
        buys = self.trades_df[self.trades_df['is_buyer_maker']]
        sells = self.trades_df[~self.trades_df['is_buyer_maker']]

        # Aggregate separately for buy and sell
        buy_agg = buys.groupby('rounded_time').agg(
            sum_asset_bought=('quantity', 'sum'),
            num_of_trades_bought=('num_trades', 'sum')
        )

        sell_agg = sells.groupby('rounded_time').agg(
            sum_asset_sold=('quantity', 'sum'),
            num_of_trades_sold=('num_trades', 'sum')
        )

        # Merge on the rounded_time
        agg_df = pd.merge(overall_avg_price, buy_agg, on='rounded_time', how='outer')
        agg_df = pd.merge(agg_df, sell_agg, on='rounded_time', how='outer').reset_index()

        # Round off float columns to desired precision
        precision = 2  # Change this as per your requirement
        agg_df = agg_df.round({'price': precision, 'sum_asset_bought': precision, 'sum_asset_sold': precision})

        # Rename the price column to avg_price
        agg_df.rename(columns={'price': 'avg_price'}, inplace=True)

        agg_df.index = agg_df['rounded_time']
        agg_df = agg_df.drop(columns=['rounded_time'])

        return agg_df


    def plot_aggregated_trades(self, agg_df):
        fig, ax1 = plt.subplots(figsize=(15, 8))

        # Line plot for average price
        ax1.plot(agg_df['rounded_time'], agg_df['avg_price'], color='b', label='Average Price', linewidth=2)
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Average Price', color='b')
        ax1.tick_params(axis='y', labelcolor='b')

        ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
        width = (agg_df['rounded_time'].iloc[1] - agg_df['rounded_time'].iloc[0]).seconds / (3 * 86400)  # Width of bars based on the time difference between entries

        # Bar plots for volumes
        ax2.bar(agg_df['rounded_time'], agg_df['sum_asset_bought'], width=width, alpha=0.6, label='Bought Volume', color='g')
        ax2.bar(agg_df['rounded_time'], -agg_df['sum_asset_sold'], width=width, alpha=0.6, label='Sold Volume', color='r')
        ax2.set_ylabel('Volume', color='g')  # Green for bought volume
        ax2.tick_params(axis='y', labelcolor='g')

        # Title and show the plot
        plt.title('Trade Dynamics Over Time')
        fig.tight_layout()  # Otherwise the right y-label is slightly clipped
        plt.legend(loc='upper left')
        plt.show()




x = TradingSimulator()
agg_trades_df = x.aggregate_trades()
agg_trades_df.to_csv(f"data/aggregate/BTCUSDT-reduced-{x.aggregation_window}-aggTrades-2023-08.csv")
# x.plot_aggregated_trades(agg_trades_df)



