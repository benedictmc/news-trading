import pandas as pd

df = pd.read_csv("news_results_all.csv", index_col=0)

APT_NEWS = "1691584214248CMaALCoNABS"

# Get when index == APT_NEWS

# apt_row = df.loc[APT_NEWS]
# print(apt_row)
top_10_max_diff = df.nlargest(10, 'max_diff_60')


def max_1_diff_analysis(df):
    top_n, count = 20, 0
    # Order by the max_diff_1 column
    df = df.sort_values(by=['max_diff_1'], ascending=False)


    for index, row in df.iterrows():
        if count == top_n:
            break
        print(row["title"])
        print(row["symbol"])
        print("Max Price 1 difference: ", row["max_diff_1"])
        print("-----")
        count += 1




large_diff = df[df.max_diff_60 > 0.1]
print("Large diff: ")
max_1_diff_analysis(large_diff)
print("*****")
print("*****")
print("*****")
print("*****")
print("All diff: ")
max_1_diff_analysis(df)

# top_10_sum_trades = df[df.symbol != "BTCUSDT"].nlargest(10, 'sum_trades_10')

# top_10_price = df.nlargest(10, 'price_change_10')

# top_30_price = df.nlargest(10, 'price_change_30')

# top_60_price = df.nlargest(10, 'price_change_60')

# # Print the 'title' column along with 'sum_trades_10' column of those rows
# # print(top_10_sum_trades[['title', 'symbol', 'sum_trades_10']])

# # print(top_10_price[['title', 'symbol', 'price_change_10']])

# # print(top_30_price[['title', 'symbol', 'price_change_30']])

# # print(top_60_price[['title', 'symbol', 'price_change_60']])



# df["price_increase_after_1"] = df["price_change_10"] - df["price_change_1"]
# top_10_price_after = df.nlargest(50, 'price_increase_after_1')

# # print(top_10_price_after[['title', 'symbol', 'price_increase_after_1']])


# print(list(top_10_price_after.index))
