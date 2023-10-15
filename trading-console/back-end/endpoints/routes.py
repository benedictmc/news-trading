from flask import render_template, jsonify, Blueprint, request, current_app as app
from tinydb import Query
from datetime import datetime
import json

endpoints = Blueprint('endpoints', __name__)

@endpoints.route('/')
def index():
    return "TODO: Add a home page TEST"


@endpoints.route('/health-ping', methods=['GET'])
def recieve_health():

    if request.method == 'GET':
        logs, timestamp = [], ""

        with open(app.config['LOG_FILE_PATH'], 'r') as log_file:
            logs = log_file.readlines()
        
        for line in reversed(logs):
            if "Ping Event" in line:
                timestamp = datetime.strptime(line[0:19], "%Y-%m-%dT%H:%M:%S")
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                break

        return jsonify({"last_ping": timestamp})


@endpoints.route('/news-events', methods=['GET'])
def get_news_events():
    news_events = []
    with open(app.config['LOG_FILE_PATH'], 'r') as log_file:
        logs = log_file.readlines()

    current_news_event = None
    for line in reversed(logs):
        if "news_event: NewsEvent" in line:
            
            # Extract the timestamp and news event details
            timestamp = datetime.strptime(line[0:19], "%Y-%m-%dT%H:%M:%S")
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            news_event_str = line.split("news_event: NewsEvent")[1].strip()
            news_event_str = news_event_str.replace("\"", '')

            symbol = news_event_str.split("binance_symbol: ")[1].split(",")[0].strip()
            time_started = news_event_str.split("time_started: ")[1].split(",")[0].strip()
            news_title = news_event_str.split("news_title: ")[1].split(",")[0].strip()
            start_price = news_event_str.split("start_price: ")[1].split(",")[0].strip()
            max_price_diff_neg = news_event_str.split("max_price_diff_neg: ")[1].split(",")[0].strip()
            max_price_diff_pos = news_event_str.split("max_price_diff_pos: ")[1].split(",")[0].strip()

            amount_of_buys_z_score = news_event_str.split("amount_of_buys_z_score: ")[1].split(",")[0].strip()
            amount_of_sells_z_score = news_event_str.split("amount_of_sells_z_score: ")[1].split(",")[0].strip()
            volume_sold_z_score = news_event_str.split("volume_sold_z_score: ")[1].split(",")[0].strip()
            volume_bought_z_score = news_event_str.split("volume_bought_z_score: ")[1].split(",")[0].strip()
            total_z_score = news_event_str.split("total_z_score: ")[1].split(",")[0].strip()
            news_id = news_event_str.split("news_id: ")[1].split(",")[0].strip()[:-2]

            news_event = {
                "symbol": symbol,
                "time_started": time_started,
                "news_title": news_title,
                "start_price": start_price,
                "timestamp": timestamp,
                "max_price_diff_neg": max_price_diff_neg,
                "max_price_diff_pos": max_price_diff_pos,
                "amount_of_buys_z_score": amount_of_buys_z_score,
                "amount_of_sells_z_score": amount_of_sells_z_score,
                "volume_sold_z_score": volume_sold_z_score,
                "volume_bought_z_score": volume_bought_z_score,
                "total_z_score": total_z_score,
                "news_id": news_id
            }

            news_events.append(news_event)

    return jsonify(news_events)
