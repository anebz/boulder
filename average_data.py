import pandas as pd
from datetime import datetime

boulder_data = pd.read_csv("~/Desktop/coding/boulder_data/boulderdata.csv")

def avg_data_day(chosen_day, chosen_gym):
    """averages all of the data for a specific gym, day, and time of the week and returns a new df"""

    #returns a number for the chosen day
    chosen_day = chosen_day.lower()
    day_dict = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5,'sunday': 6}
    day_num = day_dict[chosen_day]
    
    # returns all data for a specific day
    list_of_data = []
    for x in boulder_data.current_time.unique():
        date = x
        day = datetime.strptime(date, '%Y/%m/%d %H:%M').weekday()
        if day == day_num:
            list_of_data.append(x)
    ave_day_data = boulder_data[boulder_data['current_time'].isin(list_of_data)]

    # filters df for specific gym
    ave_data = ave_day_data[ave_day_data['gym_name'] == chosen_gym]

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


if __name__ == "__main__":

    chosen_day = input("Please select a day of the week: ")
    print()
    print(boulder_data.gym_name.unique())
    chosen_gym = input("Please select a gym: ")
    ave_data = avg_data_day(chosen_day, chosen_gym)