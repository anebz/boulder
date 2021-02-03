import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

def avg_data_day(boulderdf, day, gym):
    """averages all of the data for a specific gym, day, and time of the week and returns a new df"""
    
    # obtain only the data for the specific weekday and gym
    boulderdf['current_time'] = pd.to_datetime(boulderdf['current_time'])
    boulderdf = boulderdf[boulderdf.current_time.dt.weekday==day]
    boulderdf = boulderdf[boulderdf['gym_name'] == gym]

    # transform date to hour and minute format
    boulderdf['current_time'] = boulderdf['current_time'].dt.strftime('%H:%M')
    boulderdf.drop(['gym_name'], inplace=True, axis=1)
    #boulderdf = boulderdf[['time', 'occupancy', 'waiting', 'weather_temp', 'weather_status']]

    # iterate through the hours and obtain the means for all values
    avgdf = []
    for t in boulderdf['current_time'].unique():
        for_time = boulderdf[boulderdf['current_time'] == t]
        avgdf.append([
            t,
            round(for_time['occupancy'].mean(), 2),
            int(for_time['waiting'].mean()),
            int(for_time['weather_temp'].mean()),
            for_time['weather_status'].max()
        ])

    avgdf = pd.DataFrame(data=avgdf, columns=['time', 'occupancy', 'waiting', 'weather_temp', 'weather_status'])
    avgdf.sort_values(by=['time'], inplace=True)
    return avgdf


def plot_ave_data(df):
    fig = plt.figure()
    plt.plot('time', 'occupancy', data=df, marker='o', markerfacecolor='blue', markersize=12, color='skyblue', linewidth=4)
    plt.plot('time', 'waiting', data=df, marker='', color='olive', linewidth=2)
    plt.plot('time', 'weather_temp', data=df, marker='', color='olive', linewidth=2, linestyle='dashed', label="temp")
    plt.legend()
    return fig
