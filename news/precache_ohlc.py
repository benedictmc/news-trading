import os
import json
import requests
import pandas as pd
import datetime
from retrieve_data import fetch_data
import time

# Constants
NEWS_API_ENDPOINT = "https://news.treeofalpha.com/api"

def get_all_news(limit=500):

    if os.path.exists("data/news/all_news.json"):
        with open("data/news/all_news.json", "r") as f:
            return json.load(f)
    else:
        url =  f"{NEWS_API_ENDPOINT}/allNews"
        response = requests.get(url)

        with open("data/news/all_news.json", "w") as f:
            json.dump(response.json(), f)

        return response.json()


def get_binance_symbols(suggestions):
    symbols = []
    if suggestions == []:
        return symbols
    
    for suggestion in suggestions:
        for symbol in suggestion["symbols"]:
           if 'binance-futures' == symbol["exchange"] and 'USDT' in symbol["symbol"]:
               symbols.append(symbol["symbol"])
    return symbols


all_news = get_all_news()
print(len(all_news))

date_map = {}

def create_date_symbol_map(all_news):
    if os.path.exists("data/news/date_map.json"):
        with open("data/news/date_map.json", "r") as f:
            return json.load(f)
    date_map = {}
    for news_item in all_news[::-1]:
        news_date = pd.to_datetime(news_item["time"], unit='ms')
        date_str = str(news_date.date())

        if "suggestions" not in news_item:
            continue
        
        binance_symbols = get_binance_symbols(news_item["suggestions"])
        binance_symbol = None

        if len(binance_symbols) != 0:
            binance_symbol = binance_symbols[0] # Just take the first one for now

        if binance_symbol:
            if date_str not in date_map:
                date_map[date_str] = []

            if binance_symbol not in date_map[date_str]:
                date_map[date_str].append(binance_symbol)


    with open("data/news/date_map.json", "w") as f:
        json.dump(date_map, f)

    return date_map

# print()
date_map = create_date_symbol_map(all_news)

for date, symbols in date_map.items():
    start_time = int((datetime.datetime.strptime(date, '%Y-%m-%d').replace(tzinfo=datetime.timezone.utc)).timestamp())*1000
    end_time = start_time + int((23*60*60 + 59*60)*1000)
    start_time = pd.to_datetime(start_time, unit='ms').strftime('%Y-%m-%d %H:%M:%S')
    end_time = pd.to_datetime(end_time, unit='ms').strftime('%Y-%m-%d %H:%M:%S')

    for binance_symbol in symbols:
        ohlc_df = fetch_data(binance_symbol, "1m", start_time, end_time)


