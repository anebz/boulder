import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

import sklearn as sk
from sklearn.metrics import mean_squared_error, r2_score


def one_hot_encode_col(df: pd.DataFrame, col: str):
    df = pd.concat([df, pd.get_dummies(df[col])], axis=1)
    df.drop(col, axis=1, inplace=True)
    return df

def linear_regression(df: pd.DataFrame):

    def plot_linearity(df: pd.DataFrame, col: str):
        plt.scatter(df[col], df['occupancy'], color='green')
        plt.title(col + ' vs. occupancy', fontsize=14)
        plt.xlabel(col, fontsize=14)
        plt.ylabel('Occupancy', fontsize=14)
        plt.grid(True)
        plt.show()
        return

    # datetime processing. obtain weekday, and time as hours and minutes rounded up
    # ex. 16:45 becomes 16.75. 15:30 becomes 15.50
    df['current_time'] = pd.to_datetime(df['current_time'])
    df['weekday'] = df['current_time'].apply(lambda x: x.strftime('%A'))
    df['time'] = df['current_time'].apply(lambda x: x.hour + x.minute/60)
    df = df.drop('current_time', axis=1)

    # join occupancy and waiting into a single column
    df['occupancy'] = df.apply(lambda r: r.occupancy + r.waiting/100, axis=1)
    df.drop('waiting', axis=1, inplace=True)

    # one-hot encode the categorical variables
    df = one_hot_encode_col(df, 'gym_name')
    df = one_hot_encode_col(df, 'weekday')
    df = one_hot_encode_col(df, 'weather_status')

    # extract y from df
    y = df['occupancy'].to_numpy()
    df.drop('occupancy', axis=1, inplace=True)
    X = df.to_numpy()

    # declare linear regression model and split data
    regr = sk.linear_model.LinearRegression()
    ratio = 5
    x_train, y_train = X[:-ratio], y[:-ratio]
    x_test, y_test = X[-ratio:], y[-ratio:]

    # Train the model using the training set
    regr.fit(x_train, y_train)
    # Make predictions using the testing set
    y_pred = regr.predict(x_test)

    print('Coefficients: \n', regr.coef_)
    # The mean squared error
    print('Mean squared error: %.2f' % mean_squared_error(y_test, y_pred))
    # The coefficient of determination: 1 is perfect prediction
    print('Coefficient of determination: %.2f' % r2_score(y_test, y_pred))
    return