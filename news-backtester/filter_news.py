from dotenv import load_dotenv
import os
import pandas as pd
import json


load_dotenv()

LOCAL_LOCATION = "/home/ben/dev/news-trading/binance_downloader/local"
notable_news = []

for symbol in os.listdir(f"{LOCAL_LOCATION}/top_movements"):
    try:
        filepath = f"{LOCAL_LOCATION}/top_movements/{symbol}/2023-09/2023-09_news_signal.csv"
        df = pd.read_csv(filepath)
    except:
        continue

    df = df[(df["signal"] > 0.05) & (abs(df["avg_price_future_diff_60"]) > 0.01)]

    for index, row in df.iterrows():
        news_item = {}
        news_item["symbol"] = symbol
        news_item["date"] = row["floored_time"]
        news_item["movement_amount"] = row["signal"]
        news_item["timestamp"] = int(pd.to_datetime(row["floored_time"]).value / 1e9)
        notable_news.append(news_item)
        
notable_news_sorted = sorted(notable_news, key=lambda x: x['movement_amount'], reverse=True)

with open("notable_news.json", "w") as f:
    json.dump(notable_news_sorted, f, indent=4)