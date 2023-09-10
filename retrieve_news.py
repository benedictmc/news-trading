
import requests 
import json
import os
import time
from datetime import datetime

NEWS_API_ENDPOINT = "https://news.treeofalpha.com/api"

class GetCryptoNews():

    def __init__(self, start_time:str, end_time:str, symbol:str="BTCUSDT"):
        self.symbol = symbol
        self.start_timestamp = int(datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
        self.end_timestamp = int(datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)

        self.news = self.__load_news()

    
    def filter_news(self):
        print(f"Filtered news: {len(self.news)}")
        self.news = self.__filter_news_by_time(self.news)

        print(f"Filtered news: {len(self.news)}")
        self.news = self.__filter_news_by_symbol(self.news)

        print(f"Filtered news: {len(self.news)}")
        print(self.news[-1])
        return self.news

    def __filter_news_by_symbol(self, news):
        filtered_news = []
        
        for news_item in news:
            print(news_item)
            if 'symbols' not in news_item:
                continue
            if self.symbol in news_item['symbols']:
                filtered_news.append(news_item)

            # for suggestion in news_item['suggestions']:
            #     for symbol in suggestion['symbols']:
            #         if symbol['symbol'] == self.symbol:
            #             filtered_news.append(news_item)
            #             break
        return filtered_news
    


    def __filter_news_by_time(self, news):
        return [news_item for news_item in news if self.start_timestamp <= news_item['time'] <= self.end_timestamp]

    def __load_news(self):
            

        if not os.path.exists("local/news/all_news.json"):
            self.__retrieve_news()
        
        with open("local/news/all_news.json", "r") as f:
            return json.load(f)
        

    def __retrieve_news(self):
        url = f"{NEWS_API_ENDPOINT}/allNews"
        response = requests.get(url)

        with open(f"local/news/all_news.json", "w") as f:
            json.dump(response.json(), f, indent=4)

        return response.json()
    
start_time = "2021-08-01 00:00:00"
end_time = "2021-09-01 00:00:00"

GetCryptoNews(start_time, end_time).filter_news()