import backtrader as bt
import pandas as pd


# Custom pandas DataFrame data feed
class CustomPandasData(bt.feeds.PandasData):
    lines = ('datetime', 'open', 'high', 'low', 'close', 'volume', 'openinterest')
    params = (
        ('datetime', 0),
        ('open', 1),
        ('high', 1),
        ('low', 1),
        ('close', 1),
        ('volume', -1),
        ('openinterest', -1),
    )

class MovingAverageStrategy(bt.Strategy):
    params = (
        ('short_period', 100),
        ('long_period', 5000),
    )


    def __init__(self):
        self.short_mavg = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_period
        )
        self.long_mavg = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_period
        )
        self.crossover = bt.indicators.CrossOver(self.short_mavg, self.long_mavg)


    def next(self):
        if not self.position:  # if not in the market
            if self.crossover > 0:  # if short crosses above long
                self.buy()
        elif self.crossover < 0:  # if in the market and short crosses below long
            self.sell()



data_path = 'data/aggregate/BTCUSDT-reduced-aggTrades-2023-08.csv'
df = pd.read_csv(data_path, parse_dates=[0], delimiter=',')
df = df[['rounded_time', 'avg_price']]
# Drop rows with NaN values
df.dropna(inplace=True)

# Replace NaN or Inf with 0
df.replace([float('inf'), float('-inf'), float('nan')], 0, inplace=True)

# Group by date and save each group to a separate CSV
for date, group in df.groupby(df['rounded_time'].dt.date):

    data = CustomPandasData(dataname=group)
    cerebro = bt.Cerebro()
    cerebro.adddata(data)

    cerebro.addstrategy(MovingAverageStrategy)

    # Set our desired starting cash
    cerebro.broker.set_cash(100000)

    cerebro.broker.setcommission(commission=0.02)

    # Print starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run the strategy
    cerebro.run()

    # Print final conditions
    print('Ending Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Print the final portfolio value
    print('Final Portfolio Value: ${}'.format(cerebro.broker.getvalue()))

    # Plot the results
    cerebro.plot(volume=False)
    break

