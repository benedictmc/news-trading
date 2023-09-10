# Functions that I will use in the news part
# Taken from old code, but still want to save
# Needs refactoring

self.news = self.get_all_news()
self.news_start_time = 1682100506000
self.news_end_time = int(time.time()*1000)
self.news_second_dict = self.create_news_time_dict(self.get_all_news())
self.live_news = {}
self.expiry_dict = {}

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