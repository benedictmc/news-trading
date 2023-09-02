import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BinanceApi():

    def __init__(self):
        self.FUTURES_BASE_URL = "https://fapi.binance.com"
        self.GENERAL_BASE_URL = "https://api.binance.com"
        self.period_map = {
            "1m" : 60000,
            "5m" : 300000
        }
        self.session = self.create_session()
        
    
    @staticmethod
    def create_session():
        """Create a session with retry strategy."""
        session = requests.Session()
        
        # Define a retry strategy
        retries = Retry(
            total=5,  # Number of retries
            backoff_factor=1,  # Delay factor for retries
            status_forcelist=[429, 500, 502, 503, 504],  # Status codes to retry on
            allowed_methods=["GET"]  # HTTP methods to retry
        )
        
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        return session

    def __normalise_kline_response(self, kline_response):
        response = []
        for interval in kline_response:
            response.append({
                "timestamp" : interval[0],
                "open": interval[1],
                "high": interval[2],
                "low": interval[3],
                "close": interval[4],
                "volume": interval[5],
                "close_time": interval[6],
                "quote_asset_volume": interval[7],
                "number_of_trades": interval[8],
                "taker_buy_volume": interval[9],
                "taker_buy_quote_asset_volume": interval[10],
            })  
        return response


    def get_open_interest(self, symbol):
        api_url = "/fapi/v1/openInterest"
        request_url = f"{self.FUTURES_BASE_URL}{api_url}?symbol={symbol}"
        response = requests.get(request_url)

        if response.status_code != 200:
            print(f"Error: Code: {response.status_code}, Response: {response.text}")
            return 
        
        return response.json()


    def get_historical_open_interest(self, symbol, period, start_time=None, end_time=None):
        api_url = "/futures/data/openInterestHist"
        request_url = f"{self.FUTURES_BASE_URL}{api_url}?symbol={symbol}&period={period}&limit=500"
        
        if start_time and end_time:
            request_url = f"{request_url}&startTime={start_time}&endTime={end_time}"


        # Use session.get instead of requests.get
        response = self.session.get(request_url)

        if response.status_code != 200:
            print(f"Error: Code: {response.status_code}, Response: {response.text}")
            Exception 

        result = response.json()
        first_timestamp = result[0]['timestamp']
        print(result)
        # Needs pagination
        if start_time and first_timestamp > start_time:
            # Gets new endtime; begining of last - one period
            end_time = first_timestamp - self.period_map[period]
            result = result + self.get_historical_open_interest(symbol, period, start_time, end_time)

        return result


    def get_historical_funding_rate(self, symbol, start_time=None, end_time=None):
        api_url = "/fapi/v1/fundingRate"
        request_url = f"{self.FUTURES_BASE_URL}{api_url}?symbol={symbol}&limit=1000"
        if start_time and end_time:
            request_url = f"{request_url}&startTime={start_time}&endTime={end_time}"
        response = requests.get(request_url)
        if response.status_code != 200:
            print(f"Error: Code: {response.status_code}, Response: {response.text}")
            Exception 
        
        return response.json()


    def get_long_short_ratio(self, symbol, period, start_time=None, end_time=None):
        api_url = "/futures/data/globalLongShortAccountRatio"
        request_url = f"{self.FUTURES_BASE_URL}{api_url}?symbol={symbol}&period={period}&limit=500"
        if start_time and end_time:
            request_url = f"{request_url}&startTime={start_time}&endTime={end_time}"
        response = requests.get(request_url)

        if response.status_code != 200:
            print(f"Error: Code: {response.status_code}, Response: {response.text}")
            Exception 
        
        return response.json()


    def get_top_long_short_ratio_accounts(self, symbol, period, start_time=None, end_time=None):
        api_url = "/futures/data/topLongShortAccountRatio"
        request_url = f"{self.FUTURES_BASE_URL}{api_url}?symbol={symbol}&period={period}&limit=500"
        if start_time and end_time:
            request_url = f"{request_url}&startTime={start_time}&endTime={end_time}"
        response = requests.get(request_url)

        if response.status_code != 200:
            print(f"Error: Code: {response.status_code}, Response: {response.text}")
            Exception 
        
        return response.json()


    def get_top_long_short_ratio_positions(self, symbol, period, start_time=None, end_time=None):
        api_url = "/futures/data/topLongShortPositionRatio"
        request_url = f"{self.FUTURES_BASE_URL}{api_url}?symbol={symbol}&period={period}&limit=500"

        if start_time and end_time:
            request_url = f"{request_url}&startTime={start_time}&endTime={end_time}"

        response = requests.get(request_url)

        if response.status_code != 200:
            print(f"Error: Code: {response.status_code}, Response: {response.text}")
            Exception 
        
        return response.json()


    def get_kline_futures_data(self, symbol, period, start_time=None, end_time=None):
        api_url = "/fapi/v1/klines"
        request_url = f"{self.FUTURES_BASE_URL}{api_url}?symbol={symbol}&interval={period}&limit=1500"
        start_time_edge_case = False

        if start_time and end_time:
            if start_time == end_time:
                start_time = start_time - 60000
                start_time_edge_case = True
            request_url = f"{request_url}&startTime={start_time}&endTime={end_time}"
        
        print(f">> Request: {request_url}")
        response = requests.get(request_url)

        if response.status_code != 200:
            print(f"Error: Code: {response.status_code}, Response: {response.text}")
            raise Exception("Failed to fetch Kline data.")
        
        json_response = response.json()

        if start_time_edge_case:
            json_response = json_response[1:]
                
        result = self.__normalise_kline_response(json_response)

        if not result:  # if the result is empty, return directly
            return result
        
        last_timestamp = result[-1]['timestamp']
        
        # Pagination for next batch of data
        if last_timestamp < (end_time if end_time else float("inf")):
            new_start_time = last_timestamp + self.period_map.get(period, 0)
            
            # Fetch next batch only if the new start time is before the desired end time
            if not end_time or new_start_time < end_time:
                result += self.get_kline_futures_data(symbol, period, new_start_time, end_time)

        return result


    def get_orderbook_data(self, symbol):
        api_url = "/api/v3/depth"
        request_url = f"{self.FUTURES_BASE_URL}{api_url}?symbol={symbol}"

        response = requests.get(request_url)

        if response.status_code != 200:
            print(f"Error: Code: {response.status_code}, Response: {response.text}")
            Exception 

        return response.json()


