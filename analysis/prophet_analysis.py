#import libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import scipy.stats as stats
import math
import sklearn
import statsmodels.api as sm
from statsmodels.tsa.api import SimpleExpSmoothing
from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.offline as py
import retrieve_dataset as rd





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
            "columns":  [
                "sum_asset_bought",
                "num_of_trades_bought",
                "sum_asset_sold",
                "num_of_trades_sold"
            ]
        }
    ], 
    "signal": {
        "column": "sum_asset_sold_zscore",
        "threshold": 100,
    }
}



try:
    df = pd.read_csv('BTCUSDT_2023-09.csv', index_col=0, parse_dates=True)
except:
    df = rd.RetriveDataset("BTCUSDT", "2023-09", config).retrieve_trading_dataset()
    df.to_csv('BTCUSDT_2023-09.csv')


def prophet_fit_sec(df, prophet_model, today_index, predict_seconds, lookback_seconds):

    # segment the time frames
    baseline_ts = df['ds'][:today_index]
    baseline_y = df['y'][:today_index]
    time_difference_training = round(((df['ds'][today_index - 1] - df['ds'][0]).total_seconds())/60,2)
    time_difference_predict = round(((df['ds'][today_index + predict_seconds - 1] - df['ds'][today_index]).total_seconds())/60,2)
    if not lookback_seconds:    
        print('Use the data from {} to {} ({} minutes)'.format(df['ds'][0],
                                                            df['ds'][today_index - 1],
                                                            time_difference_training))
    else:
        baseline_ts = df['ds'][today_index - lookback_seconds:today_index]
        baseline_y = df.y[today_index - lookback_seconds:today_index]
        print('Use the data from {} to {} ({} minutes)'.format(df['ds'][today_index - lookback_seconds],
                                                            df['ds'][today_index - 1],
                                                            time_difference_training))
    print('Predict {} to {} ({} minutes)'.format(df['ds'][today_index],
                                              df['ds'][today_index + predict_seconds - 1],
                                              time_difference_predict))

    # fit the model
    prophet_model.fit(pd.DataFrame({'ds': baseline_ts.values,
                                    'y': baseline_y.values}))
    future = prophet_model.make_future_dataframe(periods=predict_seconds, freq='S')
    # make prediction
    forecast = prophet_model.predict(future)
    # generate the plot
    fig = prophet_model.plot(forecast)
    return fig, forecast, prophet_model

def get_outliers(df, forecast, today_index, predict_seconds):

    df_pred = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(predict_seconds)
    df_pred.index = df_pred['ds'].dt.to_pydatetime()
    df_pred.columns = ['ds', 'preds', 'lower_y', 'upper_y']
    df_pred['actual'] = df['y'][today_index: today_index + predict_seconds].values

    # construct a list of outliers
    outlier_index = list()
    outliers = list()
    for i in range(df_pred.shape[0]):
        actual_value = df_pred['actual'][i]
        if actual_value < df_pred['lower_y'][i] or actual_value > df_pred['upper_y'][i]:
            outlier_index += [i]
            outliers.append((df_pred.index[i], actual_value))
            print('=====')
            print('>> POTENTIAL OUTLIER')
            print('>> value: {} at {}. '.format(str(df_pred.index[i]), actual_value))

    return outliers, df_pred

def prophet_plot(df, fig, today_index, predict_seconds, lookback_seconds, outliers=list()):

    ax = fig.get_axes()[0]
    fig.set_size_inches((16, 9))

    start = today_index - 500
    end = today_index + predict_seconds
    x_pydatetime = df['ds'].dt.to_pydatetime()
    ax.plot(x_pydatetime[start:end],
            df.y[start:end],
            color='orange', label='Actual')

    for outlier in outliers:
        ax.scatter(outlier[0], outlier[1], color='red', label='Anomaly')

    if lookback_seconds:
        start = today_index - lookback_seconds
    ax.axvspan(x_pydatetime[start],
               x_pydatetime[today_index],
               color=sns.xkcd_rgb['grey'],
               alpha=0.2)

    ymin, ymax = ax.get_ylim()[0], ax.get_ylim()[1]
    ax.text(x_pydatetime[int((start + today_index) / 2)], ymin + (ymax - ymin) / 20, 'Baseline area')
    ax.text(x_pydatetime[int((today_index * 2 + predict_seconds) / 2)], ymin + (ymax - ymin) / 20, 'Prediction area')

    patch1 = mpatches.Patch(color='red', label='Anomaly')
    patch2 = mpatches.Patch(color='orange', label='Actual')
    patch3 = mpatches.Patch(color='skyblue', label='Predict and interval')
    patch4 = mpatches.Patch(color='grey', label='Baseline area')
    plt.legend(handles=[patch1, patch2, patch3, patch4])
    plt.savefig("prophet_plot.png")    


df['SMA'] = df['avg_price'].rolling(window=500).mean()
df['diff'] = df['avg_price'] - df['SMA']

df['upper'] = df['SMA'] + 60
df['lower'] = df['SMA'] - 60




df_ts = df.reset_index()
print(df_ts.head())

df_ts = df_ts[['floored_time','avg_price']]
df_ts.columns = ['ds','y']
df_ts.index = df_ts.ds

alpha=0.98

model = Prophet(interval_width=alpha, 
                yearly_seasonality=False, 
                weekly_seasonality=False,
                changepoint_prior_scale=0.2)

today_index = 7500*30
print('Cutoff date: ', df_ts.index[today_index])

predict_n = 300

fig, forecast, model = prophet_fit_sec(df_ts, model, today_index, predict_seconds=predict_n, lookback_seconds=5000)

outliers, df_pred = get_outliers(df_ts, forecast, today_index, predict_seconds=predict_n)

prophet_plot(df_ts, fig, today_index, outliers=outliers, predict_seconds=predict_n, lookback_seconds=5000)