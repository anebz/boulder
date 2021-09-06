# -*- coding: utf-8 -*-
"""
Created on Sat Aug 21 19:05:52 2021

@author: Anja
"""

import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import numpy as np


#There are two possible cases: 
#    a) the value was not recorded at the given time
#    b) the value was recorded too late

def get_missing_aquisition_timestamps(df_gym, interval = '20min', sample_start = '07:20', sample_end = '23:40'):
    '''
    Get which timestamps are missing for each day

    Parameters
    ----------
    df_gym : TYPE
        DESCRIPTION.
    interval : TYPE, optional
        DESCRIPTION. The default is '20min'.
    sample_start : TYPE, optional
        DESCRIPTION. The default is '07:20'.
    sample_end : TYPE, optional
        DESCRIPTION. The default is '23:40'.

    Returns
    -------
    values_not_recorded : TYPE
        DESCRIPTION.
    values_recorded_too_late : TYPE
        DESCRIPTION.

    '''
    series = pd.Series(data = np.array(df_gym.occupancy),
                       index = df_gym.current_time)
    series_o = pd.Series(data = np.array(df_gym.occupancy),
                         index = df_gym.current_time)
    #add a point at the start and end time if it is not starting at the start and end time of the day!
    series_startpoint = pd.Series(data = [None],
                                  index = [df_gym.current_time.min().replace(hour = int(sample_start[:2]),
                                                                                  minute = int(sample_start[3:]))
                                                ])
    series_endpoint = pd.Series(data = [None], 
                                index = [df_gym.current_time.max().replace(hour = int(sample_end[:2]),
                                                                                  minute = int(sample_end[3:]))
                                                ])
    try:
        series = series.append(series_endpoint, verify_integrity=True)
    except ValueError:
        pass
    try:
        series = series.append(series_startpoint, verify_integrity=True)
    except ValueError:
        pass
    #resort the series
    series = series.sort_index()
    #upsample it
    series_upsampled = series.resample(interval).asfreq()
    #there are times when there should be no sampling.
    series_upsampled = series_upsampled.between_time(sample_start,
                                                     sample_end,
                                         include_start = True,
                                         include_end = True)
    values_not_recorded = series_upsampled[~series_upsampled.index.isin(series_o.index)]
    values_recorded_too_late = series_o[~series_o.index.isin(series_upsampled.index)]
    return values_not_recorded, values_recorded_too_late

def number_missing_aquisitions(df_gym, interval='20min', sample_start='07:20', sample_end='23:40'):
    '''
    Prints out how many aquisition points where missed and some example times.

    Parameters
    ----------
    df : data frame for one gym only!
    interval : string, in which intervals the sampling occured (using default 20 min)
        DESCRIPTION. The default is '20min'.
    sample_start : string - when the webscraping of the boulder sites starts in the morning 
        DESCRIPTION. The default is '07:20'.
    sample_end : string - when the webscraping of the boulder sites ends in the evening 
        DESCRIPTION. The default is '23:40'.

    Returns
    -------
    Number of missing elements, an integer

    '''
    values_not_recorded, values_recorded_too_late = get_missing_aquisition_timestamps(df_gym, 
                                                                                      interval,
                                                                                      sample_start,
                                                                                      sample_end)
    print(len(values_not_recorded),' values were not recorded!')
    print(len(values_recorded_too_late),' values were recorded too late!')
    
    return len(values_not_recorded)+len(values_recorded_too_late)

def add_missing_timestamps(df, interval='20min', sample_start='07:20', sample_end='23:40'):
    '''
    Add missing timestamps (with all other values being NaN)
    Parameters
    ----------
    df : pd.Dataframe of the different bouldering gyms
        DESCRIPTION.
    interval : TYPE, optional
        DESCRIPTION. The default is '20min'.
    sample_start : TYPE, optional
        DESCRIPTION. The default is '07:20'.
    sample_end : TYPE, optional
        DESCRIPTION. The default is '23:40'.

    Returns
    -------
    df_new : the data frame with the missing timestamps for the gyms added 
    (but all other values being NaN)

    '''


    for gym in df.gym_name.unique():
        #how many values are missing for this gym?
        df_gym = df[df.gym_name == gym].sort_values(by = 'current_time',
                                                    ascending=True)
        values_not_recorded, values_recorded_too_late = get_missing_aquisition_timestamps(df_gym, 
                                                                                          interval,
                                                                                          sample_start,
                                                                                          sample_end)
        #add the values not recorded
        values_to_append = [{'current_time': time,'gym_name': gym} for time in values_not_recorded.index]
        df = df.append(values_to_append,
                       ignore_index=True)

    return df

def fill_nan_values(df):
    '''
    fill Nan values with an interpolation
    
    All Nan-values will be filled, those outside of the data will be interpolated.
    Should they be negative for the occupancy or waiting, they will be set to zero.
    The weather status will take the nearest value

    Parameters
    ----------
    df : dataframe

    Returns
    -------
    df : dataframe 
    '''
    #fill the missing values with a nearest interpolation of the same day!
    for gym in df.gym_name.unique():
        df_gym = df[df.gym_name == gym].sort_values(by = 'current_time',
                                                    ascending = True)
        #get the timestamps where values are missing
        timestamps = df_gym.current_time[df_gym.occupancy.isnull()]
        for index, timestamp in timestamps.items():
            #get a series of the day in question
            time_mask = (df_gym.current_time.dt.day == timestamp.day)&\
                (df_gym.current_time.dt.month == timestamp.month)&\
                    (df_gym.current_time.dt.year == timestamp.year)
            df_gym_day = df_gym[time_mask]
            #drop the nans of this series
            df_gym_day_noNan = df_gym_day.dropna()
            #interpolate the occupancy, waiting and weather_temp
            #xavlues need to be real valued!
            x_values = (df_gym_day_noNan.current_time-pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
            #only do this if there are enough x_values >5
            if len(x_values)>5:
                for column in ['occupancy', 'waiting', 'weather_temp']:
                    # this might work with the dev version of scipy:
                    
                    func = interp1d(x_values,
                                    df_gym_day_noNan[column],
                                    kind = 'linear',
                                  bounds_error = False, 
                                  fill_value = 'extrapolate')
                    
                    #fill in the interpolated value!
                    timestamp_unix = (timestamp-pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
                    values = func(timestamp_unix)
                    if column in ['occupancy', 'waiting']:
                        values[values<0] = 0
                    df.loc[index, column] = values

            else:
                #just take the mean, as 4 points is not enough to properly interpolate (probably just the ends anyway)
                for column in ['occupancy', 'waiting', 'weather_temp']:
                    df.loc[index,column] = df_gym_day_noNan[column].mean()
            #for the weather it is a bit more complicated. just take the nearest one
            for column in ['weather_status']:
                #take as a default the one from before, if it doesn't exist, the one after
                #add the timestamp to the noNan and sort it
                df_gym_day_oneNan = df_gym_day_noNan.append(df.loc[index],
                                                            ignore_index = False)
                df_gym_day_oneNan = df_gym_day_oneNan.sort_values(by = 'current_time',
                                                                  ascending = True)
                #Case 1: it is at the beginning:
                if df_gym_day_oneNan.iloc[0].isnull().sum() == 1:
                    shift=-1
                else:
                    shift=+1
                df_gym_day_oneNan_shift = df_gym_day_oneNan.shift(shift)
                df.loc[index,column] = df_gym_day_oneNan_shift.loc[index, column]
                
    return df

def remove_excess_values(df, interval = '20min', sample_start = '07:20', sample_end = '23:40'):
    '''
    remove rows which where not measured at the set intervals

    Parameters
    ----------
    df : TYPE
        DESCRIPTION.
    interval : TYPE, optional
        DESCRIPTION. The default is '20min'.
    sample_start : TYPE, optional
        DESCRIPTION. The default is '07:20'.
    sample_end : TYPE, optional
        DESCRIPTION. The default is '23:40'.

    Returns
    -------
    df : pd dataFrame

    '''
    for gym in df.gym_name.unique():
        df_gym = df[df.gym_name == gym].sort_values(by = 'current_time',
                                                    ascending = True)
        values_not_recorded, values_recorded_too_late = get_missing_aquisition_timestamps(df_gym, 
                                                                                          interval,
                                                                                          sample_start,
                                                                                          sample_end)
        #remove the values_recorded_too_late
        cond1 = (df.current_time.isin(values_recorded_too_late.index))
        cond2 = (df.gym_name==gym)
        cond3 = (cond1 & cond2)
        df = df.drop(df[cond3].index)
    return df


def correct_bouldering_dataframe(df, interval = '20min', sample_start = '07:20', sample_end = '23:40'):
    '''
    Recast boulder dataframe into another time-sampling and interpolate the data

    Will interpolate data which has been left out
    will remove data which has been measured too late
    ----------
    df : Boulder dataframe
    interval : TYPE, optional
        DESCRIPTION. The default is '20min'.
    sample_start : TYPE, optional, when does measuring start?
        DESCRIPTION. The default is '07:20'.
    sample_end : TYPE, optional, when does measuring stop?
        DESCRIPTION. The default is '23:40'.

    Returns
    -------
    pandas dataframe

    '''

    return remove_excess_values(fill_nan_values(add_missing_timestamps(df)),
                                interval,
                                sample_start,
                                sample_end)


