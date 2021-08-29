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

def get_missing_aquisition_timestamps(df_gym, interval='20min',sample_start='07:20',sample_end='23:40'):
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
    series=pd.Series(data=np.array(df_gym.occupancy),index=df_gym.current_time)
    series_o=pd.Series(data=np.array(df_gym.occupancy),index=df_gym.current_time)
    #add a point at the start and end time if it is not starting at the start and end time of the day!
    series_startpoint=pd.Series(data=[None],index=[df_gym.current_time.min().replace(hour=int(sample_start[:2]),
                                                                                  minute=int(sample_start[3:]))
                                                ])
    series_endpoint=pd.Series(data=[None],index=[df_gym.current_time.max().replace(hour=int(sample_end[:2]),
                                                                                  minute=int(sample_end[3:]))
                                                ])
    try:
        series=series.append(series_endpoint,verify_integrity=True)
    except ValueError:
        pass
    try:
        series=series.append(series_startpoint,verify_integrity=True)
    except ValueError:
        pass
    #resort the series
    series=series.sort_index()
    #upsample it
    series_upsampled=series.resample(interval).asfreq()
    #there are times when there should be no sampling.
    series_upsampled=series_upsampled.between_time(sample_start,sample_end,
                                         include_start=True,
                                         include_end=True)
    values_not_recorded=series_upsampled[~series_upsampled.index.isin(series_o.index)]
    values_recorded_too_late=series_o[~series_o.index.isin(series_upsampled.index)]
    return values_not_recorded,values_recorded_too_late

def number_missing_aquisitions(df_gym, interval='20min',sample_start='07:20',sample_end='23:40'):
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
    values_not_recorded,values_recorded_too_late=get_missing_aquisition_timestamps(df_gym, interval,sample_start,sample_end)
    print(len(values_not_recorded),' values were not recorded!')
    print(len(values_recorded_too_late),' values were recorded too late!')
    
    return len(values_not_recorded)+len(values_recorded_too_late)

def add_missing_timestamps(df,interval='20min',sample_start='07:20',sample_end='23:40'):
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
        #print('Missing values for gym ',gym)
        #h=number_missing_aquisitions(df[df.gym_name==gym].sort_values(by='current_time',ascending=True))
        df_gym=df[df.gym_name==gym].sort_values(by='current_time',ascending=True)
        values_not_recorded,values_recorded_too_late=get_missing_aquisition_timestamps(df_gym, interval,sample_start,sample_end)
        #add the values not recorded
        values_to_append=[{'current_time':time,'gym_name':gym} for time in values_not_recorded.index]
        #print('For gym ',gym, len(values_to_append), ' values appended!')
        df=df.append(values_to_append,ignore_index=True)

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
        print('gym',gym)
        df_gym=df[df.gym_name==gym].sort_values(by='current_time',ascending=True)
        #get the timestamps where values are missing
        timestamps=df_gym.current_time[df_gym.occupancy.isnull()]
        for index, timestamp in timestamps.items():
            #get a series of the day in question
            time_mask=(df_gym.current_time.dt.day==timestamp.day)&\
                (df_gym.current_time.dt.month==timestamp.month)&\
                    (df_gym.current_time.dt.year==timestamp.year)
            df_gym_day=df_gym[time_mask]
            #drop the nans of this series
            df_gym_day_noNan=df_gym_day.dropna()
            #interpolate the occupancy, waiting and weather_temp
            #xavlues need to be real valued!
            x_values=(df_gym_day_noNan.current_time-pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
            #only do this if there are enough x_values >5
            if len(x_values)>5:
                for column in ['occupancy','waiting','weather_temp']:
                    # this might work with the dev version of scipy:
                    
                    func=interp1d(x_values,df_gym_day_noNan[column],kind='linear',
                                  bounds_error=False, 
                                  fill_value='extrapolate')
                    
                    #fill in the interpolated value!
                    timestamp_unix=(timestamp-pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
                    #print(timestamps)
                    values=func(timestamp_unix)
                    if column in ['occupancy','waiting']:
                        values[values<0]=0
                    df.loc[index,column]=values

            else:
                #just take the mean, as 4 points is not enough to properly interpolate (probably just the ends anyway)
                for column in ['occupancy','waiting','weather_temp']:
                    df.loc[index,column]=df_gym_day_noNan[column].mean()
            #for the weather it is a bit more complicated. just take the nearest one
            for column in ['weather_status']:
                #take as a default the one from before, if it doesn't exist, the one after
                #add the timestamp to the noNan and sort it
                df_gym_day_oneNan=df_gym_day_noNan.append(df.loc[index],ignore_index=False)
                df_gym_day_oneNan=df_gym_day_oneNan.sort_values(by='current_time',ascending=True)
                #Case 1: it is at the beginning:
                if df_gym_day_oneNan.iloc[0].isnull().sum()==1:
                    #print('beginning it is!')
                    shift=-1
                else:
                    shift=+1
                #print(df_gym_day_oneNan[['current_time',column]])
                df_gym_day_oneNan_shift=df_gym_day_oneNan.shift(shift)
                #print(df_gym_day_oneNan_shift[['current_time',column]])
                df.loc[index,column]=df_gym_day_oneNan_shift.loc[index,column]
                
    return df

def remove_excess_values(df,interval='20min',sample_start='07:20',sample_end='23:40'):
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
        df_gym=df[df.gym_name==gym].sort_values(by='current_time',ascending=True)
        values_not_recorded,values_recorded_too_late=get_missing_aquisition_timestamps(df_gym, interval,sample_start,sample_end)
        print('########################')
        print('number of values_to_be_dropped ',len(values_recorded_too_late))
        #remove the values_recorded_too_late
        cond1=(df.current_time.isin(values_recorded_too_late.index))
        cond2=(df.gym_name==gym)
        cond3=(cond1 & cond2)
        df=df.drop(df[cond3].index)
    return df


def correct_bouldering_dataframe(df,interval='20min',sample_start='07:20',sample_end='23:40'):
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
    
    
    return remove_excess_values(fill_nan_values(add_missing_timestamps(df)),interval,sample_start,sample_end)



#testing and documenting the different functions
import unittest
import random



class Testget_missing_aquisition_timestamps(unittest.TestCase):
    
    def gaussian(self,n,sigma,shift):
        gauss=np.exp(-0.5*((n-shift)/sigma)**2)
        return gauss

    def plot_gaussian(self):
        import matplotlib.pyplot as plt
        n=50
        plt.figure()
        x=np.array(np.arange(0,n,1))
        plt.plot(x,self.gaussian(x,5,len(x)/2))
        plt.show()
        
    def get_testset(self):
        #make a test df with 3 missing values for 2 gymns, missing values at the beginning,middle, end
        #for three days
        day1=pd.date_range(start="2018-01-01 07:20:00", end="2018-01-01 23:40:00", freq="20min")
        day2=pd.date_range(start="2018-01-02 07:20:00", end="2018-01-02 23:40:00", freq="20min")
        day3=pd.date_range(start="2018-01-03 07:20:00", end="2018-01-03 23:40:00", freq="20min")
        days=[day1,day2,day3,day1,day2,day3]
        gym1='muenchen-ost'
        gym2='frankfurt'
        gyms_n=[gym1,gym1,gym1,gym2,gym2,gym2]
        gyms=[[gyms_n[g] for n in day] for g,day in enumerate(days)]
        #occupancies=[[float(random.randint(0,100)) for n in day] for day in days]
        #making a gauss for occupancies
        occupancies=[self.gaussian(np.arange(0,len(day),1),len(day)/5,len(day)/2) for day in days]
        #waitings=[[float(random.randint(0,15)) for n in day] for day in days]
        waitings=[self.gaussian(np.arange(0,len(day),1),len(day)/5,len(day)/2) for day in days]
        temps=[[float(random.randint(0,15)) for n in day] for day in days]
        temps=[self.gaussian(np.arange(0,len(day),1),len(day)/5,len(day)/2)-0.5 for day in days]
        #statuss=[[random.choice(['Clouds', 'Rain', 'Drizzle', 'Clear', 'Thunderstorm', 'Mist']) for n in day] for day in days]
        statuss=[[random.choice(['Clouds', 'Rain', 'Drizzle', 'Clear', 'Thunderstorm', 'Mist'])]*len(day) for day in days]
        #print('jo',len(days),len(gyms),len(days[0]),len(occupancies[0]))
        dfs=[pd.DataFrame({'current_time': days[i],
                           'gym_name':gyms[i],
                           'occupancy':occupancies[i],
                           'waiting':waitings[i],
                           'weather_temp':temps[i],
                           'weather_status':statuss[i]
                           }) for i in range(len(days))]
        df=dfs[0]
        df=df.append(dfs[1:],ignore_index=True)
        #print(df.shape,dfs[0].shape)
        return df
    
    
    def test_testset_types(self):
        df=self.get_testset()
        types=df.dtypes
        self.assertEqual(types['current_time'],'<M8[ns]')
        self.assertEqual(types['gym_name'],'object')
        self.assertEqual(types['weather_status'],'object')
        self.assertEqual(types['occupancy'],'float64')
        self.assertEqual(types['waiting'],'float64')
        self.assertEqual(types['weather_temp'],'float64')
    
    def test_number_missing(self):
        df=self.get_testset()
        for gym in df['gym_name'].unique():
            df_gym=df[df.gym_name==gym]
            #delete a value at the beginning
            df_gym=df_gym.drop([df_gym.index[0]])
            values_not_recorded,values_recorded_too_late=get_missing_aquisition_timestamps(df_gym, interval='20min',sample_start='07:20',sample_end='23:40')
            self.assertEqual(len(values_not_recorded),1)
            #delete also a value at the end
            df_gym=df_gym.drop([df_gym.index[-1]])
            values_not_recorded,values_recorded_too_late=get_missing_aquisition_timestamps(df_gym, interval='20min',sample_start='07:20',sample_end='23:40')
            self.assertEqual(len(values_not_recorded),2)
            #delete also a value in the middle
            df_gym=df_gym.drop([df_gym.index[5]])
            values_not_recorded,values_recorded_too_late=get_missing_aquisition_timestamps(df_gym, interval='20min',sample_start='07:20',sample_end='23:40')
            self.assertEqual(len(values_not_recorded),3)

    def test_testset(self):
        df=self.get_testset()
        self.assertEqual(df.shape,(300,6))

    def test_add_missing_timestamps(self):
        df=self.get_testset()
        #remove 8 values at random
        for n in range(8):
            df=df.drop([df.index[random.randint(0,len(df)-1)]])
        df2=add_missing_timestamps(df,interval='20min',sample_start='07:20',sample_end='23:40')
        self.assertEqual(300,len(df2))
    
    def test_fill_nan(self):
        df=self.get_testset()
        #remove 8 values at random
        for n in range(8):
            df=df.drop([df.index[random.randint(0,len(df)-1)]])
        df2=add_missing_timestamps(df,interval='20min',sample_start='07:20',sample_end='23:40')
        df2=fill_nan_values(df2)
        self.assertEqual(0,df2.isnull().sum().sum())
      
    def test_drop_additional(self):
        df=self.get_testset()
        #change the time of 8 values at random
        for n in range(8):
            df.current_time[random.randint(0,len(df)-1)]+=pd.to_timedelta(16, unit='min')
        df2=add_missing_timestamps(df,interval='20min',sample_start='07:20',sample_end='23:40')
        df2=fill_nan_values(df2)
        print('okay. testing')
        df2=remove_excess_values(df2,interval='20min',sample_start='07:20',sample_end='23:40')
        self.assertEqual(300,len(df2))

    def test_correct_value_recovered(self):
        #test whether the fill nan algorithm puts in values that make sense!
        df_o=self.get_testset()
        df=df_o[:]
        #remove 8 values at random
        dropped=[]
        for n in range(8):
            drop=df.index[random.randint(0,len(df)-1)]
            dropped.append(df.loc[drop])
            df=df.drop([drop])
        
        df2=add_missing_timestamps(df,interval='20min',sample_start='07:20',sample_end='23:40')
        df2=fill_nan_values(df2)
        #get the values it recovered:
        recovered=[]
        for n,drop in enumerate(dropped):
            recovered.append(df2[(df2.gym_name==drop.gym_name)&
                                 (df2.current_time==drop.current_time)])
        '''
        #in case of visual inspection
        plt.figure()
        gym='frankfurt'
        plt.subplot(311)
        plt.plot(df_o[df_o.gym_name==gym].current_time,df_o[df_o.gym_name==gym].occupancy,'o',label='o')
        plt.subplot(312)
        plt.plot(df[df.gym_name==gym].current_time,df[df.gym_name==gym].occupancy,'.',label='drop')
        plt.subplot(313)
        plt.plot(df2[df2.gym_name==gym].current_time,df2[df2.gym_name==gym].occupancy,'*',label='recovered')
        plt.legend()
        plt.show()
        '''
        for n,rec in enumerate(recovered):
            self.assertEqual(rec.current_time.iloc[0],dropped[n].current_time)
            #check wether in 10% limit
            for column in ['occupancy','waiting']:
                self.assertTrue((rec[column].iloc[0]<dropped[n][column]*1.1)&
                                 (rec[column].iloc[0]>dropped[n][column]*0.9))
            column='weather_temp'
            ass=(np.abs(rec[column].iloc[0])<np.abs(dropped[n][column])*1.1)&(np.abs(rec[column].iloc[0])>np.abs(dropped[n][column])*0.9)
            self.assertTrue(ass)
            #print(rec.current_time.iloc[0],'....',dropped[n].current_time)
            self.assertEqual(rec.weather_status.iloc[0],dropped[n].weather_status)
        self.assertEqual(0,df2.isnull().sum().sum())
  

if __name__ == '__main__':
    unittest.main()
