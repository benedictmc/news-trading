import requests
import json
import pandas as pd
import mplfinance as mpf
import numpy as np
from retrieve_data import fetch_data
import os
import datetime
from pprint import pprint

# Constants
NEWS_API_ENDPOINT = "https://news.treeofalpha.com/api"
NEWS_RESULTS = []
SYMBOL_MAP = {
    "CURVE": "CRV",
}
INTERVALS = [1, 5, 10, 30, 60]

NOTABLE_IDS = [ "1691584214248CMaALCoNABS"]

def get_news(limit=500):
    url =  f"{NEWS_API_ENDPOINT}/news?limit={limit}"
    response = requests.get(url)
    return response.json()


def get_all_news(limit=500):

    if os.path.exists("data/news/all_news.json"):
        with open("data/news/all_news.json", "r") as f:
            return json.load(f)
    else:
        url =  f"{NEWS_API_ENDPOINT}/allNews"
        response = requests.get(url)
        return response.json()


def calculate_change(df, minutes):
    if len(df) > minutes:
        return ((df['close'].iloc[minutes] - df['close'].iloc[0]) / df['close'].iloc[0])
    else:
        return None


def get_binance_symbols(suggestions):
    symbols = []
    if suggestions == []:
        return symbols
    
    for suggestion in suggestions:
        for symbol in suggestion["symbols"]:
           if 'binance-futures' == symbol["exchange"] and 'USDT' in symbol["symbol"]:
               symbols.append(symbol["symbol"])
    return symbols
        

def compute_asset_changes(df, news_date, intervals):
    """
    Compute price changes and additional statistics for given intervals.
    
    Parameters:
    df (DataFrame): The input data frame containing historical price data
    news_date (Timestamp): The date and time at which the news was published
    intervals (list): List of time intervals (in minutes) after the news_date
    
    Returns:
    dict: A dictionary containing the computed results for each interval
    """
    
    # Get the close price at the time of the news
    news_price = df.loc[news_date, 'open']
    changes = {}
    
    for interval in intervals:
        # Compute the start and end time for the interval
        start_time = news_date 
        end_time = news_date + pd.Timedelta(minutes=interval)
        
        # Filter the data to include only rows within the interval
        interval_data = df.loc[start_time:end_time]
        try:
            if not interval_data.empty:
                # Compute the required statistics
                future_price = interval_data.loc[end_time, 'close'] if end_time in interval_data.index else -1
                price_change = round((future_price - news_price) / news_price, 4)
                sum_trades = interval_data['number_of_trades'].sum()
                max_high = interval_data['high'].max()
                max_low = interval_data['low'].min()
                sum_volume = interval_data['volume'].sum()
                max_diff = max(round(abs((future_price - max_high) / news_price), 4) , round(abs((future_price - max_low) / news_price), 4))

            else:
                # If no data is available for the interval, set all statistics to 0 or NaN as appropriate
                price_change = 0
                sum_trades = 0
                max_high = float('nan')
                sum_volume = 0
            
            # Store the results for this interval
            changes[interval] = {
                'price_change': price_change,
                'sum_trades': sum_trades,
                'max_high': max_high,
                'sum_volume': sum_volume, 
                'max_diff': max_diff
            }
        except Exception as e:
            print(e)
            return
    
    return changes


def handle_news_item(news_item, notables_only=False, rerun=False):
    
    news_id = news_item["_id"]

    if not rerun and news_id in NEWS_ID_SET:
        return

    if notables_only and news_id not in NOTABLE_IDS:
        return
    

    news_title = news_item["title"].replace('\n', ' ')
    news_time = news_item["time"]
    news_source = news_item["source"]
    

    if "suggestions" not in news_item:
        return
    
    binance_symbols = get_binance_symbols(news_item["suggestions"])
    binance_symbol = None

    if len(binance_symbols) != 0:
        binance_symbol = binance_symbols[0] # Just take the first one for now

    # Floor the news time to the nearest minute
    minute_of_news = news_time - (news_time % 60000)
    

    if binance_symbol != None:
        plot_news = False

        start_time = pd.to_datetime(minute_of_news - (60000*60), unit='ms').strftime('%Y-%m-%d %H:%M:%S')
        end_time = pd.to_datetime(minute_of_news + (60000*60), unit='ms').strftime('%Y-%m-%d %H:%M:%S')
        ohlc_df = fetch_data(binance_symbol, "1m", start_time, end_time)

        news_date = pd.to_datetime(minute_of_news, unit='ms')
        news_price_open = ohlc_df.loc[news_date, 'open']
        news_price_close = ohlc_df.loc[news_date, 'close']
        ohlc_df['news'] = np.nan
        
        try:
            ohlc_df.loc[news_date, 'news'] = ohlc_df.loc[news_date, 'open']  # placing triangle at close price
        except KeyError:
            pass
        

        changes = compute_asset_changes(ohlc_df, news_date, INTERVALS)

        result = {
            "id": news_id,
            "title": news_title,
            "source": news_source,
            "symbol": binance_symbol,
            "time": news_time,
            "price_open" : news_price_open,
            "price_close" : news_price_close,
        }

        for interval in INTERVALS:
            result[f"price_change_{interval}"] = changes[interval]["price_change"]
            result[f"sum_trades_{interval}"] = changes[interval]["sum_trades"]
            result[f"max_high_{interval}"] = changes[interval]["max_high"]
            result[f"sum_volume_{interval}"] = changes[interval]["sum_volume"]
            result[f"max_diff_{interval}"] = changes[interval]["max_diff"]

        if result["max_diff_60"] > 0.1:
            pprint(result)
            plot_news = True

        if plot_news:
            ap = [mpf.make_addplot(ohlc_df['news'], type='scatter', markersize=100, marker='^', color='r')]
            mpf.plot(ohlc_df[['open', 'high', 'low', 'close']], type='candle', style='charles', title=f'News: {binance_symbol} on {news_date}', volume=False, addplot=ap)


        NEWS_RESULTS.append(result)



def compile_news():

    kb_interrupt = False
            
    try:
        NEWS_ID_SET = set()

        if os.path.exists("news_results_all.csv"):
            news_df = pd.read_csv("news_results_all.csv", index_col=0)
            if len(news_df) != 0:
                NEWS_ID_SET = set(news_df.index.values)

        news = get_all_news()
            
        for news_item in news[::-1]:
            handle_news_item(news_item, notables_only=False, rerun=False)

    except KeyboardInterrupt:
        print("Interrupted by user. Saving the progress...")
        kb_interrupt = True

    finally:
        df = pd.DataFrame(NEWS_RESULTS)
        # Save to CSV regardless of whether an exception occurred or not
        if kb_interrupt or len(df) != 0:
            df.index = df['id']
            df = df.drop(columns=['id'])

            if len(NEWS_ID_SET) != 0:
                df = pd.concat([news_df, df])
                
            df.to_csv("news_results_all.csv")
            
            print("File saved.")
        else:
            raise 