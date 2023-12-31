from backtest_trades import Backtester
from retrieve_dataset import RetriveDataset
import copy
import json


core_columns = [
    "sum_asset_bought",
    "num_of_trades_bought",
    "sum_asset_sold",
    "num_of_trades_sold"
]

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
            "type": "zscore",
            "columns": core_columns
        }
    ], 
    "signal": {
        "column": "sum_asset_sold_zscore",
        "threshold": 100,
    }
}


results = []


for threshold in [39]:
    for col in ["num_of_trades_sold"]:

# for threshold in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]:
#     for col in core_columns:

        symbol = "LTCUSDT"
        date = "2023-08"

        variation_config = copy.deepcopy(config)
        variation_config['signal']['column'] = col + '_zscore'
        variation_config['signal']['threshold'] = threshold

        print("================================")
        print(f"> Signal is {variation_config['signal']['column']} when threshold over {variation_config['signal']['threshold']}")

        df = RetriveDataset(symbol, date, variation_config).retrieve_trading_dataset()
        bt = Backtester(df, symbol, date)
        bt.run(should_plot=True)
        bt.save_trade_list()

        print("================================")
        print("> DONE")
        print("> Total Trades: ", len(bt.trade_list))
        print("> Total TradeScore: ", round(bt.total_trade_score, 4))
        print("> Positive Trades: ", bt.positive_trades)
        print("> Negative Trades: ", bt.negative_trades)
        print("================================")

        result = {
            "symbol": symbol,
            "date": date,
            "signal": f"{variation_config['signal']['column']} when threshold over {variation_config['signal']['threshold']}",
            "total_trades": len(bt.trade_list),
            "total_trade_score": round(bt.total_trade_score, 4),
            "positive_trades": bt.positive_trades,
            "negative_trades": bt.negative_trades,
        }
        results.append(result)

        with open("grid_search_results.json", "w") as f:
            json.dump(results, f, indent=4)