import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

def avg_data_day(boulderdf, day, gym):
    """averages all of the data for a specific gym, day, and time of the week and returns a new df"""
    
    # returns all data for a specific day
    list_of_data = []
    for date in boulderdf.current_time.unique():
        local_day = datetime.strptime(date, '%Y/%m/%d %H:%M').weekday()
        if local_day == day:
            list_of_data.append(date)
    ave_day_data = boulderdf[boulderdf['current_time'].isin(list_of_data)]

    # filters df for specific gym
    ave_data = ave_day_data[ave_day_data['gym_name'] == gym]

    # clean df to have time in a separate column, prep for next step
    ave_data[['date', 'time']] = ave_data['current_time'].str.split(' ', 1, expand=True)
    ave_data.drop(['gym_name', 'current_time', 'date'], inplace=True, axis=1)
    ave_data = ave_data[['time', 'occupancy', 'waiting', 'weather_temp', 'weather_status']]

    # create new df with average data
    final_df = {
        'time': [],
        'occupancy': [],
        'waiting': [],
        'weather_temp': [],
        'weather_status': []
    }

    for t in ave_data.time.unique():
        for_time = ave_data[ave_data['time'] == t]
        final_df['time'].append(t)
        final_df['occupancy'].append(for_time['occupancy'].mean())
        final_df['waiting'].append(for_time['waiting'].mean())
        final_df['weather_temp'].append(for_time['weather_temp'].mean())
        final_df['weather_status'].append(for_time['weather_status'].max())

    final_df = pd.DataFrame(data=final_df)
    final_df.sort_values(by=['time'], inplace=True)

    return final_df


def plot_ave_data(df):
    fig = plt.figure()
    plt.plot('time', 'occupancy', data=df, marker='o', markerfacecolor='blue', markersize=12, color='skyblue', linewidth=4)
    plt.plot('time', 'waiting', data=df, marker='', color='olive', linewidth=2)
    plt.plot('time', 'weather_temp', data=df, marker='', color='olive', linewidth=2, linestyle='dashed', label="temp")
    plt.legend()
    return fig
