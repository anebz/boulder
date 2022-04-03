# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 17:41:35 2021

@author: Anja
"""


#testing and documenting the different functions
from fix_missing_values import *
import unittest
import random



class Testget_missing_aquisition_timestamps(unittest.TestCase):
    
    def gaussian(self, n, sigma, shift):
        return np.exp(-0.5*((n-shift)/sigma)**2)

    def plot_gaussian(self):
        import matplotlib.pyplot as plt
        n = 50
        plt.figure()
        x = np.array(np.arange(0,n,1))
        plt.plot(x, self.gaussian(x, 5, len(x)/2))
        plt.show() 
        
    def get_testset(self):
        #make a test df with 3 missing values for 2 gymns, missing values at the beginning,middle, end
        #for three days
        day1 = pd.date_range(start = "2018-01-01 07:20:00", end = "2018-01-01 23:40:00", freq = "20min")
        day2 = pd.date_range(start = "2018-01-02 07:20:00", end = "2018-01-02 23:40:00", freq = "20min")
        day3 = pd.date_range(start = "2018-01-03 07:20:00", end = "2018-01-03 23:40:00", freq = "20min")
        days = [day1, day2 ,day3, day1, day2, day3]
        gym1 = 'muenchen-ost'
        gym2 = 'frankfurt'
        gyms_n = [gym1, gym1, gym1, gym2, gym2, gym2]
        gyms = [[gyms_n[g] for _ in day] for g,day in enumerate(days)]
        #occupancies=[[float(random.randint(0,100)) for n in day] for day in days]
        #making a gauss for occupancies
        occupancies = [self.gaussian(np.arange(0,len(day),1),len(day)/5,len(day)/2) for day in days]
        #waitings=[[float(random.randint(0,15)) for n in day] for day in days]
        waitings  =[self.gaussian(np.arange(0,len(day),1),len(day)/5,len(day)/2) for day in days]
        temps = [[float(random.randint(0,15)) for _ in day] for day in days]
        temps = [self.gaussian(np.arange(0,len(day),1),len(day)/5,len(day)/2)-0.5 for day in days]
        #statuss=[[random.choice(['Clouds', 'Rain', 'Drizzle', 'Clear', 'Thunderstorm', 'Mist']) for n in day] for day in days]
        statuss = [[random.choice(['Clouds', 'Rain', 'Drizzle', 'Clear', 'Thunderstorm', 'Mist'])]*len(day) for day in days]
        #print('jo',len(days),len(gyms),len(days[0]),len(occupancies[0]))
        dfs = [pd.DataFrame({'current_time': days[i],
                           'gym_name': gyms[i],
                           'occupancy': occupancies[i],
                           'waiting': waitings[i],
                           'weather_temp': temps[i],
                           'weather_status': statuss[i]
                           }) for i in range(len(days))]
        df = dfs[0]
        df = df.append(dfs[1:], 
                       ignore_index=True)
        return df
    
    
    def test_testset_types(self):
        df = self.get_testset()
        types = df.dtypes
        self.assertEqual(types['current_time'],
                         '<M8[ns]')
        self.assertEqual(types['gym_name'],
                         'object')
        self.assertEqual(types['weather_status'],
                         'object')
        self.assertEqual(types['occupancy'],
                         'float64')
        self.assertEqual(types['waiting'],
                         'float64')
        self.assertEqual(types['weather_temp'],
                         'float64')
    
    def test_number_missing(self):
        df = self.get_testset()
        for gym in df['gym_name'].unique():
            df_gym = df[df.gym_name == gym]
            #delete a value at the beginning
            df_gym = df_gym.drop([df_gym.index[0]])
            values_not_recorded, values_recorded_too_late = get_missing_aquisition_timestamps(df_gym, 
                                                                                              interval='20min',
                                                                                              sample_start='07:20',
                                                                                              sample_end='23:40')
            self.assertEqual(len(values_not_recorded),1)
            #delete also a value at the end
            df_gym = df_gym.drop([df_gym.index[-1]])
            values_not_recorded, values_recorded_too_late = get_missing_aquisition_timestamps(df_gym, 
                                                                                              interval='20min',
                                                                                              sample_start='07:20',
                                                                                              sample_end='23:40')
            self.assertEqual(len(values_not_recorded),2)
            #delete also a value in the middle
            df_gym = df_gym.drop([df_gym.index[5]])
            values_not_recorded, values_recorded_too_late = get_missing_aquisition_timestamps(df_gym, 
                                                                                              interval='20min',
                                                                                              sample_start='07:20',
                                                                                              sample_end='23:40')
            self.assertEqual(len(values_not_recorded),3)

    def test_testset(self):
        df = self.get_testset()
        self.assertEqual(df.shape, (300,6))

    def test_add_missing_timestamps(self):
        df = self.get_testset()
        #remove 8 values at random
        for _ in range(8):
            df = df.drop([df.index[random.randint(0, len(df)-1)]])
        df2 = add_missing_timestamps(df,
                                     interval='20min',
                                     sample_start='07:20',
                                     sample_end='23:40')
        self.assertEqual(300, len(df2))
    
    def test_fill_nan(self):
        df = self.get_testset()
        #remove 8 values at random
        for _ in range(8):
            df = df.drop([df.index[random.randint(0, len(df)-1)]])
        df2 = add_missing_timestamps(df,
                                     interval='20min',
                                     sample_start='07:20',
                                     sample_end='23:40')
        df2 = fill_nan_values(df2)
        self.assertEqual(0, df2.isnull().sum().sum())
      
    def test_drop_additional(self):
        df = self.get_testset()
        #change the time of 8 values at random
        for _ in range(8):
            df.current_time[random.randint(0, len(df)-1)]+=pd.to_timedelta(16, unit='min')
        df2 = add_missing_timestamps(df,
                                     interval='20min',
                                     sample_start='07:20',
                                     sample_end='23:40')
        df2 = fill_nan_values(df2)
        df2 = remove_excess_values(df2,
                                   interval='20min',
                                   sample_start='07:20',
                                   sample_end='23:40')
        self.assertEqual(300, len(df2))

    def test_correct_value_recovered(self):
        #test whether the fill nan algorithm puts in values that make sense!
        df_o = self.get_testset()
        df = df_o[:]
        #remove 8 values at random
        dropped = []
        for _ in range(8):
            drop = df.index[random.randint(0, len(df)-1)]
            dropped.append(df.loc[drop])
            df = df.drop([drop])

        df2 = add_missing_timestamps(df,
                                     interval='20min',
                                     sample_start='07:20',
                                     sample_end='23:40')
        df2 = fill_nan_values(df2)
        #get the values it recovered:
        recovered = [
            df2[
                (df2.gym_name == drop.gym_name)
                & (df2.current_time == drop.current_time)
            ]
            for drop in dropped
        ]

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
        for n, rec in enumerate(recovered):
            self.assertEqual(rec.current_time.iloc[0], dropped[n].current_time)
            #check wether in 10% limit
            for column in ['occupancy', 'waiting']:
                self.assertTrue((rec[column].iloc[0]<dropped[n][column]*1.1)&
                                 (rec[column].iloc[0]>dropped[n][column]*0.9))
            column = 'weather_temp'
            ass = (np.abs(rec[column].iloc[0])<np.abs(dropped[n][column])*1.1) & (np.abs(rec[column].iloc[0])>np.abs(dropped[n][column])*0.9)
            self.assertTrue(ass)
            self.assertEqual(rec.weather_status.iloc[0],
                             dropped[n].weather_status)
        self.assertEqual(0,
                         df2.isnull().sum().sum())

    def test_weather_status_recovered(self):
        df = self.get_testset()
        df.weather_status = 'Rain'
        location_to_change = random.randint(0, len(df)-1)
        
        timing_loc = df.loc[location_to_change].current_time
        gym_loc = df.loc[location_to_change].gym_name
        cond_gym = (df.gym_name == gym_loc)
        cond_time = (df.current_time == timing_loc)
        
        iloc_loc = np.where(df[cond_gym].current_time == timing_loc)[0][0]
       
        df.loc[location_to_change-1:location_to_change+1,'weather_status'] = 'Clouds'

        drop = df.index[location_to_change]
        df = df.drop([drop])        
        df2 = add_missing_timestamps(df,
                                     interval='20min',
                                     sample_start='07:20',
                                     sample_end='23:40')
        df2 = fill_nan_values(df2)

        self.assertEqual(df2[cond_gym & cond_time].weather_status.iloc[0],'Clouds')

if __name__ == '__main__':
    unittest.main()
