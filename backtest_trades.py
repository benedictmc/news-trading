import backtrader as bt
import pandas as pd

class SimpleStrategy(bt.Strategy):
    params = (
        ('threshold', 2.0),
        ('holding_period', 3)
    )

    def __init__(self):
        self.data_close = self.datas[0].close
        self.data_pct_change = self.datas[0].abs_percentage_change_20sec
        self.order = None
        self.buy_price = None
        self.counter = 0

    def next(self):
        if self.counter > 0:
            self.counter -= 1

            if self.counter == 0:
                self.sell()
                self.order = None

        elif self.data_pct_change[0] > self.params.threshold:
            self.order = self.buy()
            self.buy_price = self.data_close[0]
            self.counter = self.params.holding_period

# Sample data
data = {
    'close': [26118.399701],
    'abs_percentage_change_20sec': [2.859281]
}
df = pd.DataFrame(data, index=pd.to_datetime(['2023-08-17 21:43:29']))

# Convert DataFrame to Backtrader's data feed format
data_feed = bt.feeds.PandasData(dataname=df)

# Create a Backtrader Cerebro engine
cerebro = bt.Cerebro()

# Add data feed to the engine
cerebro.adddata(data_feed)

# Add strategy to the engine
cerebro.addstrategy(SimpleStrategy)

# Set our desired starting cash
cerebro.broker.set_cash(100000)

# Set the commission (assuming no commission for simplicity)
cerebro.broker.setcommission(commission=0.0)

# Print starting conditions
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

# Run the strategy
cerebro.run()

# Print final conditions
print('Ending Portfolio Value: %.2f' % cerebro.broker.getvalue())