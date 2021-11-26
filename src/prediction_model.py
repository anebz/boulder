import pickle
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt


def one_hot_encode_col(df: pd.DataFrame, col: str) -> pd.DataFrame:
    df = pd.concat([df, pd.get_dummies(df[col])], axis=1)
    df = df.drop(col, axis=1)
    return df

def preprocess(df: pd.DataFrame) -> (np.array, np.array):
    # datetime processing. obtain weekday, and time as hours and minutes rounded up
    # ex. 16:45 becomes 16.75. 15:30 becomes 15.50
    df['time'] = pd.to_datetime(df['time'])
    df['weekday'] = df['time'].apply(lambda x: x.strftime('%A'))
    df['time'] = df['time'].apply(lambda x: round(x.hour + x.minute/60, 2))
    df.drop('time', axis=1, inplace=True)

    # join occupancy and waiting into a single column
    df['occupancy'] = df.apply(lambda r: r.occupancy + r.waiting/10, axis=1)
    df.drop('waiting', axis=1, inplace=True)

    # one-hot encode the categorical variables
    df = one_hot_encode_col(df, 'gym_name')
    df = one_hot_encode_col(df, 'weekday')
    df = one_hot_encode_col(df, 'weather_status')

    # extract X,y from df
    y = df['occupancy'].to_numpy()
    X = df.drop('occupancy', axis=1).to_numpy()

    print(f"Shape of training data: {X.shape}")

    return X, y

def train_xgb_model(X, y):
    import xgboost as xgb
    # Show all messages, including ones pertaining to debugging
    xgb.set_config(verbosity=2)
    model = xgb.XGBRegressor(objective='reg:squarederror', verbosity=1)
    model.fit(X, y)
    return model


def train_sklearn_model(X, y):
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.model_selection import cross_val_score, RepeatedKFold
    model = GradientBoostingRegressor()
    cv = RepeatedKFold(n_splits=10, n_repeats=3, random_state=1)
    n_scores = cross_val_score(model, X, y, scoring='neg_mean_absolute_error', cv=cv, n_jobs=-1, error_score='raise')
    print('MAE: %.3f (%.3f)' % (np.mean(n_scores), np.std(n_scores)))
    model.fit(X, y)
    return model

def model_predict(X, model):
    return model.predict(X)


boulderdf = pd.read_csv("boulderdata.csv")
X, y = preprocess(boulderdf)
model = train_sklearn_model(X, y)
pickle.dump(model, open("../model.dat", "wb"))

print(model.predict([X[0]]))