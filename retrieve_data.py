
import pandas as pd
import os
from binance_api import BinanceApi  # Assuming this is your Binance API wrapper
import time

# Binance API client
binance_client = BinanceApi()

def fetch_data(symbol, period, start_time, end_time, verbose=False):
    start_time = pd.Timestamp(start_time)
    end_time = pd.Timestamp(end_time)
    date_range = pd.date_range(start=start_time.date(), end=end_time.date(), freq='D')
    all_data = []
    debug = False
    
    if verbose:
        print(f"Fetching data from {start_time} to {end_time}")

    if f"Fetching data from {start_time} to {end_time}" == "Fetching data from 2023-08-18 23:00:00 to 2023-08-19 01:00:00":
        print("VERBOSE")
        debug = True
    
    for date in date_range:
        retrive_date = date.date()

        if debug:
            pass
            # exit()

        # Default values for the retrieval times
        retrive_start_hour = 0 
        retrive_start_minute = 0
        retrive_end_hour = 23  
        retrive_end_minute = 59
        
        # Check if the date is the start date
        if start_time.date() == retrive_date:
            retrive_start_hour = start_time.hour  
            retrive_start_minute = start_time.minute 

        # Check if the date is the end date
        if end_time.date() == retrive_date:
            retrive_end_hour = end_time.hour  
            retrive_end_minute = end_time.minute 

        retrive_start_time = int(pd.Timestamp(
            year=date.year, month=date.month, day=date.day,
            hour=retrive_start_hour, minute=retrive_start_minute
        ).timestamp() * 1000)
        
        retrive_end_time = int(pd.Timestamp(
            year=date.year, month=date.month, day=date.day,
            hour=retrive_end_hour, minute=retrive_end_minute
        ).timestamp() * 1000)

        existing_data = load_data_from_file(symbol, retrive_date)
        
        if existing_data is None or existing_data.empty:
            if verbose:
                print(f"No local data found for {retrive_date}, downloading...")
            new_data = get_data(symbol, period, retrive_start_time, retrive_end_time)
            time.sleep(0.5)
            if new_data is not None:
                save_data_to_file(new_data, symbol, retrive_date)
        else:
            if verbose:
                print(f"Loaded local data for {retrive_date}")  
            new_data = existing_data
            retrive_start_time_ts = pd.to_datetime(retrive_start_time, unit='ms')
            retrive_end_time_ts = pd.to_datetime(retrive_end_time, unit='ms')

            # If retrive_start_time not in new_data
            # Download data from retrive_start_time to earliest time in new_data
            if retrive_start_time_ts < new_data.index.min():
                if verbose:
                    print(f"Missing data at the start for {retrive_date}, downloading...")

                missing_data_start = get_data(symbol, period, retrive_start_time, int(new_data.index.min().timestamp() * 1000))
                time.sleep(0.5)
                # Remove last row of missing_data_start as it will be a duplicate
                missing_data_start = missing_data_start.iloc[:-1]
                new_data = pd.concat([missing_data_start, new_data])
                save_data_to_file(new_data, symbol, retrive_date)
                
            # If retrive_end_time not in new_data
            # Download data from latest time in new_data to retrive_end_time
            if retrive_end_time_ts > new_data.index.max():
                if verbose:
                    print(f"Missing data at the end for {retrive_date}, downloading...")

                missing_data_end = get_data(symbol, period, int(new_data.index.max().timestamp() * 1000), retrive_end_time)
                time.sleep(0.5)
                # Remove first row of missing_data_end as it will be a duplicate
                missing_data_end = missing_data_end.iloc[1:]
                new_data = pd.concat([new_data, missing_data_end])
                save_data_to_file(new_data, symbol, retrive_date)

            new_data = new_data[(new_data.index >= retrive_start_time_ts) & (new_data.index <= retrive_end_time_ts)]
            
        all_data.append(new_data)

    full_data = pd.concat(all_data)
    for col in full_data.columns:
        if col != 'timestamp':
            full_data[col] = pd.to_numeric(full_data[col], errors='coerce')

    return full_data

def load_data_from_file(symbol, date):
    year, month, day = date.year, date.month, date.day
    file_path = f'data/coins/{symbol}/{year}/{month:02}/{day:02}.csv'
    # print(f"Attempting to load data from file: {file_path}")
    
    if os.path.exists(file_path):
        return pd.read_csv(file_path, index_col=0, parse_dates=True)
    else:
        return None

def get_data(symbol, period, start_time_unix, end_time_unix):
    data = binance_client.get_kline_futures_data(symbol, period, start_time_unix, end_time_unix)
    
    if data == []:
        print("No data returned from Binance API")
        return None
    
    df = pd.DataFrame(data)
    
    if 'timestamp' in df.columns:
        df.index = pd.to_datetime(df.pop('timestamp'), unit='ms')
    else:
        print("No 'timestamp' column in the data. Columns available:")
        print(df.columns)
    
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    
    return df

def save_data_to_file(data, symbol, date):
    year, month, day = date.year, date.month, date.day
    file_path = f'data/coins/{symbol}/{year}/{month:02}/{day:02}.csv'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # print(f"Saving data to file: {file_path}")
    data.to_csv(file_path)

# # Example usage
# symbol = 'BTCUSDT'
# period = '1m'
# start_time = '2023-08-15 02:00:00'
# end_time = '2023-08-15 07:00:00'
# data = fetch_data(symbol, period, start_time, end_time)