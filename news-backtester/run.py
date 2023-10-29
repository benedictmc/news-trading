from retrieve_binance.retrieve_dataset import RetriveDataset
from retrieve_binance.plot_data import plot_data

symbol = "XRPUSDT"
date = "2023-09"
config = {
    "columns": [
        "avg_price",
        "sum_asset_bought",
        "num_of_trades_bought",
        "sum_asset_sold",
        "num_of_trades_sold",
    ], 
    "features": [
        {
            "type": "news_signal"
        }
    ]
}

retrieve_dataset = RetriveDataset(symbol=symbol, date=date, config=config)

df = retrieve_dataset.retrieve_trading_dataset()
print(df.columns)


plot_data(df, symbol, add_marker='news_signal', title=f"Plot for {symbol}")