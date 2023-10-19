import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from retrieve_dataset import RetriveDataset
import numpy as np


# Load your data
# Assume df is your DataFrame
df = pd.read_csv('all_ideal_trades.csv')
# Drop first column
df = df.drop(df.columns[0], axis=1)

# Split your data into training and testing sets
drop_cols = [
    "isIdealTrade",
    "signal",
    "avg_price_5s",
    "avg_price_20s",
    "avg_price_60s",
    "avg_price_15m",
    "avg_price_30m",
    "avg_price_60m",
    "pct_change_5s",
    "pct_change_20s",
    "pct_change_60s",
    "pct_change_15m",
    "pct_change_30m",
    "pct_change_60m"
]

y = df['isIdealTrade']
X = df.drop(drop_cols, axis=1)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale your data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train your model
clf = RandomForestClassifier(random_state=42)
clf.fit(X_train_scaled, y_train)




# Evaluate your model
# y_pred = clf.predict(X_test_scaled)
# print('Accuracy:', accuracy_score(y_test, y_pred))
# print('Confusion Matrix:', confusion_matrix(y_test, y_pred))
# importance = clf.feature_importances_

# for i, col in enumerate(X.columns):
#     print(f'{col}: {importance[i]}')

# print('Feature Importances:', clf.feature_importances_)



trading_data = RetriveDataset("APTUSDT", "2023-08")
df = trading_data.retrieve_trading_dataset()
df = df.drop('signal', axis=1)

unseen_X = scaler.fit_transform(df)

unseen_y_pred = clf.predict(unseen_X)
print(unseen_y_pred)

# Count number of 1s
print(np.count_nonzero(unseen_y_pred == 1))
# Count number of 0s
print(np.count_nonzero(unseen_y_pred == 0))