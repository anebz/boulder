import datetime
import numpy as np
import pandas as pd
import plotly.graph_objects as go


def avg_data_day(boulderdf: pd.DataFrame, day: int, gym: str) -> pd.DataFrame:
    '''
    Input: dataframe with all data, weekday (0: Monday, 6: Sunday), gym name
    Output: dataframe with average data for the given input parameters
    '''
    
    # obtain only the data for the specific weekday and gym
    boulderdf['time'] = pd.to_datetime(boulderdf['time'])
    boulderdf = boulderdf[boulderdf.time.dt.weekday==day]
    boulderdf = boulderdf[boulderdf['gym_name'] == gym]

    if len(boulderdf) == 0:
        return boulderdf

    # transform date to hour and minute format
    boulderdf['time'] = boulderdf['time'].dt.strftime('%H:%M')

    # divide into 2 dfs in DAV gyms
    if 'DAV' in gym:
        boulderdf[['bouldern', 'klettern']] = boulderdf['occupancy'].str.split('/', 1, expand=True)
        boulderdf['bouldern'] = pd.to_numeric(boulderdf['bouldern'])
        boulderdf['klettern'] = pd.to_numeric(boulderdf['klettern'])
        # obtain the time and occupancy means
        avgdf = [[t, round(boulderdf[boulderdf['time'] == t]['bouldern'].mean()), round(boulderdf[boulderdf['time'] == t]['klettern'].mean())]\
                for t in boulderdf['time'].unique()]

        avgdf = pd.DataFrame(data=avgdf, columns=['time', 'bouldern', 'klettern'])
    else:
        # normal case, only one occupancy info
        # obtain the time and occupancy means
        avgdf = [[t, round(boulderdf[boulderdf['time'] == t]['occupancy'].mean())]\
                for t in boulderdf['time'].unique()]

        avgdf = pd.DataFrame(data=avgdf, columns=['time', 'occupancy'])
    avgdf.sort_values(by=['time'], inplace=True)
    return avgdf


def given_day(boulderdf: pd.DataFrame, date: str, gym: str) -> pd.DataFrame:
    '''
    Input: dataframe with all data, a specific date, gym name
    Output: dataframe with all of the data for the given input parameters
    '''
    # make conversion from streamlit-type datetime to format in df
    date = date.replace('-', '/')
    # obtain only the data for the specific weekday and gym
    boulderdf = boulderdf[boulderdf['time'].str.contains(date)]
    boulderdf = boulderdf[boulderdf['gym_name'] == gym]
    boulderdf.drop(['gym_name'], axis=1, inplace=True)

    if len(boulderdf) == 0:
        return boulderdf

    # transform date to hour and minute format
    boulderdf['time'] = boulderdf['time'].apply(lambda x: x.split()[1])

    # divide occupancy into 2 columns in DAV gyms
    if 'DAV' in gym:
        boulderdf[['bouldern', 'klettern']] = boulderdf['occupancy'].str.split('/', 1, expand=True)
        boulderdf['bouldern'] = pd.to_numeric(boulderdf['bouldern'])
        boulderdf['klettern'] = pd.to_numeric(boulderdf['klettern'])
        boulderdf.drop('occupancy', axis=1, inplace=True)

    # sort the data by time
    boulderdf.sort_values(by=['time'], inplace=True)
    return boulderdf


def plot_data(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    # dash options include 'dash', 'dot', and 'dashdot
    if 'occupancy' in df:
        fig.add_trace(go.Scatter(x=df.time, y=df.occupancy, name='Occupancy', line=dict(color='firebrick', width=4)))
    elif 'bouldern' in df and 'klettern' in df:
        fig.add_trace(go.Scatter(x=df.time, y=df.bouldern, name='Bouldern', line=dict(color='blue', width=4)))
        fig.add_trace(go.Scatter(x=df.time, y=df.klettern, name='Klettern', line=dict(color='orange', width=4)))
    if 'weather_temp' in df:
        fig.add_trace(go.Scatter(x=df.time, y=df.weather_temp, name='Temperature', line=dict(color='green', width=4, dash='dot')))

    fig['layout']['yaxis'].update(title='', range=[-5, 105], autorange=False)
    fig.update_layout(width=800)
    return fig


def preprocess_current_data(boulderdf: pd.DataFrame, selected_gym: str, current_time: datetime.date):

    with open('onehotlist.txt') as fin:
        onehotlist = fin.read().splitlines()
    today_data = [0] * len(onehotlist)

    # parse today's weekday
    today_weekday = current_time.strftime('%A')
    today_data[onehotlist.index(today_weekday)] = 1

    # obtain minute to predict = current_min + 20min (next interval)
    next_min = round(current_time.hour + (current_time.minute + 20)/60, 2)
    today_data[onehotlist.index('time')] = next_min

    # one-hot selected gym
    today_data[onehotlist.index(selected_gym)] = 1

    # obtain latest weather
    latest_gym_entry = boulderdf.loc[boulderdf['gym_name'] == selected_gym].iloc[0]
    # one-hot weather status
    today_data[onehotlist.index('weather_temp')] = latest_gym_entry['weather_temp']
    today_data[onehotlist.index(latest_gym_entry['weather_status'])] = 1

    # convert to numpy array
    X_today = [np.asarray(today_data)]
    return X_today
