
import requests 
import json
import os
import time
from datetime import datetime, timezone 
import pandas as pd
import numpy
from dotenv import load_dotenv

load_dotenv()

LOCAL_LOCATION = os.getenv("LOCAL_LOCATION")
if LOCAL_LOCATION == None:
    raise Exception("> retrieve_news: LOCAL_LOCATION not set. Please make .env file with LOCAL_LOCATION filepath")

NEWS_API_ENDPOINT = "https://news.treeofalpha.com/api"

class GetCryptoNews():

    def __init__(self, start_time:str, end_time:str, symbol:str="BTC_USDT"):
        print("=== GetCryptoNews ===")
        print("> Initializing GetCryptoNews...")
        self.symbol = symbol

        self.start_timestamp = int(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp() * 1000)
        self.end_timestamp = int(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp() * 1000)
        self.symbol_set = set()
        self.news_location = LOCAL_LOCATION

        self.news = self.__load_news()

    
    def filter_news(self):
        print(f"> Filtered news: {len(self.news)}")
        self.news = self.__filter_news_by_time(self.news)

        print(f"> Filtered news: {len(self.news)}")
        self.news = self.__filter_news_by_symbol(self.news)

        print(f"> Filtered news: {len(self.news)}")

        return self.news


    def __filter_news_by_symbol(self, news):
        filtered_news = []

        target_suggestion_symbol = self.symbol.replace("_", "")

        for news_item in news:

            if 'symbols' in news_item and self.symbol in news_item['symbols']:
                filtered_news.append(news_item)

            if 'suggestions' in news_item:
                for suggestion in news_item['suggestions']:
                    for suggestion_symbol in suggestion['symbols']:
                        if suggestion_symbol['symbol'] == target_suggestion_symbol:
                            filtered_news.append(news_item)
                            break
                       

        return filtered_news
    

    def create_news_df(self):
        # Create index from start to end time
        index = pd.date_range(start= pd.to_datetime(self.start_timestamp, unit='ms'), end=pd.to_datetime(self.end_timestamp, unit='ms'), freq='1s')
        news_df = pd.DataFrame(index=index)
        
        news_times = [pd.to_datetime(int(news_item['time']/1000), unit='s') for news_item in self.news] 

        news_df['news_signal'] = 0
        news_df.loc[news_times, 'news_signal'] = 1

        return news_df

    

    def __filter_news_by_time(self, news):
        return [news_item for news_item in news if self.start_timestamp <= news_item['time'] <= self.end_timestamp]

    def __load_news(self):

        current_timestamp = int(time.time())
        if not os.path.exists(f"{self.news_location}/news/"):
            os.makedirs(f"{self.news_location}/news", exist_ok=True)
            self.__retrieve_news()
        
        else:
            has_all_news = [f if 'all_news' in f else None for f in os.listdir(f"{self.news_location}/news")]

            if len(has_all_news) > 0:
                last_updated = int(has_all_news[0].split("_")[2].replace(".json", ""))

                if current_timestamp - last_updated > 60 * 60 * 24:
                    self.__retrieve_news()
        
        has_all_news = [f if 'all_news' in f else None for f in os.listdir(f"{self.news_location}/news")]

        with open(f"{self.news_location}/news/{has_all_news[0]}", "r") as f:
            return json.load(f)
        

    def __retrieve_news(self):
        url = f"{NEWS_API_ENDPOINT}/allNews"
        response = requests.get(url)
        current_timestamp = int(time.time())

        with open(f"{self.news_location}/news/all_news_{current_timestamp}.json", "w") as f:
            json.dump(response.json(), f, indent=4)

        return response.json()
    




