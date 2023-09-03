import os
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import dotenv
import requests
import zipfile
from azure.core.exceptions import ResourceNotFoundError
import time

dotenv.load_dotenv()
ACCOUNT_KEY = os.environ['AZURE_STORAGE_ACCOUNT_KEY']
ACCOUNT_URL = os.environ['AZURE_STORAGE_ACCOUNT_URL']

BLOB_CLIENT = BlobServiceClient(account_url=ACCOUNT_URL, credential=ACCOUNT_KEY)

SYMBOLS = [ 'LRCUSDT','BTCUSDT','ZECUSDT','EOSUSDT','SOLUSDT','XEMUSDT','OPUSDT','SNXUSDT','1INCHUSDT','TRXUSDT','QTUMUSDT','AGIXUSDT','RUNEUSDT','FLOWUSDT','BNBUSDT','HFTUSDT','APTUSDT','ANKRUSDT','DOGEUSDT','ASTRUSDT','RDNTUSDT','STXUSDT','CTKUSDT','ETHUSDT','NEARUSDT','TUSDT','IOTXUSDT','GRTUSDT','UNIUSDT','ZRXUSDT','DYDXUSDT','ICPUSDT','NEOUSDT','BNXUSDT','SANDUSDT','EGLDUSDT','SSVUSDT','GTCUSDT','MASKUSDT','AMBUSDT','DARUSDT','CELOUSDT','AAVEUSDT','HBARUSDT','ARBUSDT','SXPUSDT','ANTUSDT','ZENUSDT','ICXUSDT','XTZUSDT','YFIUSDT','RSRUSDT','PEOPLEUSDT','DGBUSDT','LINKUSDT','GALUSDT','FTMUSDT','FXSUSDT','TLMUSDT','CELRUSDT','SUSHIUSDT','ALPHAUSDT','ARPAUSDT','HOOKUSDT','MINAUSDT','COTIUSDT','JOEUSDT','ENSUSDT','WOOUSDT','INJUSDT','SKLUSDT','USDCUSDT','IMXUSDT','SFPUSDT','DASHUSDT','MAGICUSDT','PERPUSDT','CTSIUSDT','CHZUSDT','QNTUSDT','LEVERUSDT','IOTAUSDT','IOSTUSDT','WAVESUSDT','TOMOUSDT','BLZUSDT','C98USDT','VETUSDT','ZILUSDT','GMTUSDT','DOTUSDT','ROSEUSDT','LDOUSDT','XLMUSDT','CFXUSDT','LITUSDT','XVSUSDT','OCEANUSDT','BANDUSDT','HOTUSDT','LTCUSDT','AVAXUSDT','ENJUSDT','GALAUSDT','BATUSDT','FETUSDT','BALUSDT','FILUSDT','KAVAUSDT','RNDRUSDT','LPTUSDT','AUDIOUSDT','ALGOUSDT','XRPUSDT','OGNUSDT','GMXUSDT','ACHUSDT','ONTUSDT','KLAYUSDT','REEFUSDT','AXSUSDT','HIGHUSDT','LINAUSDT','ALICEUSDT','DUSKUSDT','FLMUSDT','PHBUSDT','ATOMUSDT','MATICUSDT','LQTYUSDT','STORJUSDT','CKBUSDT','KNCUSDT','MKRUSDT','APEUSDT','API3USDT','NKNUSDT','RVNUSDT','CHRUSDT','MANAUSDT','CRVUSDT','STMXUSDT','ADAUSDT','ATAUSDT','STGUSDT','ARUSDT','IDUSDT','RLCUSDT','THETAUSDT','BLURUSDT','ONEUSDT','TRUUSDT','TRBUSDT','COMPUSDT','IDEXUSDT','SUIUSDT','EDUUSDT','MTLUSDT','1000PEPEUSDT','1000FLOKIUSDT','DENTUSDT','BCHUSDT','1000XECUSDT','JASMYUSDT','UMAUSDT','BELUSDT','1000SHIBUSDT','RADUSDT','XMRUSDT','1000LUNCUSDT','SPELLUSDT','KEYUSDT','COMBOUSDT','UNFIUSDT','CVXUSDT','ETCUSDT','MAVUSDT','MDTUSDT','XVGUSDT','NMRUSDT','BAKEUSDT','WLDUSDT','PENDLEUSDT','ARKMUSDT','AGLDUSDT','YGGUSDT','SEIUSDT' ]


def does_blob_exist(container_file_path):
    blob_client = BlobClient(account_url=ACCOUNT_URL, container_name="binancedata", blob_name=container_file_path, credential=ACCOUNT_KEY)

    # Try to get blob properties
    try:
        blob_client.get_blob_properties()
        return True
    except ResourceNotFoundError:
        return False



def upload_to_blob(local_file_path, container_file_path):
    try:
        blob_containter = BLOB_CLIENT.get_blob_client(container="binancedata", blob=container_file_path)

        with open(local_file_path, 'rb') as data:
            blob_containter.upload_blob(data, overwrite=True)

        print("File uploaded successfully!")

    except Exception as e:
        print(e)



def download_binance_data(symbol, data_type, interval, date, save_path="local"):
    success = False
    try:
        request_url = f"https://data.binance.vision/data/futures/um/{interval}/{data_type}/{symbol}/{symbol}-{data_type}-{date}.zip"
        print(f"Downloading {symbol}-{data_type}-{date}.zip")

        # Send GET request
        response = requests.get(request_url, stream=True)
        response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code.

        # Get the total file size from headers
        total_size = int(response.headers.get('Content-Length', 0))
        downloaded_size = 0


        # Define file path
        file_path = os.path.join(save_path, f"{symbol}-{data_type}-{date}.zip")
        
        # Save the response content as a binary file
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192): 
                file.write(chunk)
                downloaded_size += len(chunk)
                percentage_completed = (downloaded_size / total_size) * 100
                print(f"Downloaded: {downloaded_size} of {total_size} bytes ({percentage_completed:.2f}%  complete)", end='\r')
        
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(save_path)

        print("File unzipped successfully!")

        # Deleting the zip file
        os.remove(file_path)
        print(f"Deleted zip file: {file_path}")
        success = True

    except Exception as e:
        print(e)

    finally:
        return success
    

def retrieve_agg_trades(symbol, date, interval="monthly"):
    data_type = "aggTrades"

    local_file_path = f"local/{symbol}-{data_type}-{date}.csv"
    container_file_path = f"{data_type}/{interval}/{symbol}/{symbol}-{data_type}-{date}.csv"

    if does_blob_exist(container_file_path):
        return

    # Downloading data
    success = download_binance_data(symbol, data_type, interval, date)

    if not success:
        return

    # Save to blob
    upload_to_blob(local_file_path, container_file_path)

    # Deleting the csv file
    os.remove(local_file_path)

    print(f"Deleted csv file: {local_file_path}")

