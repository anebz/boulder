import numpy as np
import pandas as pd
import xgboost as xgb
from datetime import datetime
import matplotlib.pyplot as plt

# Show all messages, including ones pertaining to debugging
xgb.set_config(verbosity=2)


def one_hot_encode_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = pd.concat([df, pd.get_dummies(df[col])], axis=1)
    df.drop(col, axis=1, inplace=True)
    return df


def preprocess(df: pd.DataFrame) -> (np.array, np.array):

    # datetime processing. obtain weekday, and time as hours and minutes rounded up
    # ex. 16:45 becomes 16.75. 15:30 becomes 15.50
    df['current_time'] = pd.to_datetime(df['current_time'])
    df['weekday'] = df['current_time'].apply(lambda x: x.strftime('%A'))
    df['time'] = df['current_time'].apply(lambda x: x.hour + x.minute/60)
    df.drop('current_time', axis=1, inplace=True)

    # join occupancy and waiting into a single column
    df['occupancy'] = df.apply(lambda r: r.occupancy + r.waiting/100, axis=1)
    df.drop('waiting', axis=1, inplace=True)

    # one-hot encode the categorical variables
    df = one_hot_encode_col(df, 'gym_name')
    df = one_hot_encode_col(df, 'weekday')
    df = one_hot_encode_col(df, 'weather_status')

    # extract X,y from df
    y = df['occupancy'].to_numpy()
    X = df.drop('occupancy', axis=1).to_numpy()

    return X, y

def train_model(X, y):
    model = xgb.XGBRegressor(objective='reg:squarederror', verbosity=1)
    model.fit(X, y)
    return model

def model_predict(X, model):
    return model.predict(X)
