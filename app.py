import os
import pytz
import boto3
import pickle
import datetime
import pandas as pd
import streamlit as st
from src.visualize_data import avg_data_day, given_day, preprocess_current_data, plot_data

bucketname = 'bboulderdataset'
dfname = 'boulderdata.csv'
modelname = 'model.dat'
s3 = boto3.client('s3')

gyms = {
    'Bad Tölz DAV': 'https://www.kletterzentrum-badtoelz.de',
    'Berlin Magicmountain': 'https://www.magicmountain.de/preise',
    'Braunschweig Fliegerhalle': 'https://www.fliegerhalle-bs.de',
    'Dortmund Boulderwelt':'https://www.boulderwelt-dortmund.de',
    'Frankfurt Boulderwelt': 'https://www.boulderwelt-frankfurt.de',
    'Gilching DAV': 'https://www.kbgilching.de',
    'Munich East Boulderwelt': 'https://www.boulderwelt-muenchen-ost.de',
    'Munich West Boulderwelt': 'https://www.boulderwelt-muenchen-west.de',
    'Munich South Boulderwelt': 'https://www.boulderwelt-muenchen-sued.de',
    'Munich Einstein': 'https://muenchen.einstein-boulder.com',
    'Munich Freimann DAV': 'https://www.kbfreimann.de',
    'Munich Thalkirchen DAV': 'https://www.kbthalkirchen.de',
    'Munich Heavens Gate': 'https://www.heavensgate-muc.de/',
    'Regensburg Boulderwelt': 'https://www.boulderwelt-regensburg.de',
    'Regensburg DAV': 'https://www.kletterzentrum-regensburg.de'
}

def st_given_day(boulderdf):
    # ask user for gym and date input
    st.markdown("""
    ## How full is my gym today?\n
    Due to Corona, gyms have reduced their capacity. Once the Corona capacity is reached, people have to wait to enter the gym.\n
    You can see the occupancy as a percentage of Corona capacity and the weather in the plot.\n
    If the occupancy is above 100%, that means the Corona capacity has been filled and people are waiting to enter the gym.
    """)

    selected_gym = st.radio('Select a gym', sorted(list(boulderdf['gym_name'].unique())))
    today = datetime.date.today()
    # get first available date, the last row in the dataframe
    first_date = datetime.datetime.strptime(boulderdf.iloc[-1]['time'], "%Y/%m/%d %H:%M")
    selected_date = st.date_input('Selected date', today, min_value=first_date, max_value=today)

    st.markdown(f"Showing results for [{selected_gym}]({gyms[selected_gym]})")

    # display the data for the given day
    givendaydf = given_day(boulderdf, str(selected_date), selected_gym)
    if givendaydf.empty:
        st.error('There is no data to show for this day. The gym might be closed')
    else:
        st.plotly_chart(plot_data(givendaydf), width=800)
    return selected_gym, selected_date

def get_current_time():
    # https://stackoverflow.com/a/60169568/4569908
    dt = datetime.datetime.now()
    timeZone = pytz.timezone("Europe/Berlin")
    aware_dt = timeZone.localize(dt)
    if aware_dt.dst() != datetime.timedelta(0,0):
        #summer time
        dt += datetime.timedelta(hours=2)
    else:
        #winter time
        dt += datetime.timedelta(hours=1)
    dt = dt.strftime("%Y/%m/%d %H:%M")

    #round to the nearest 20min interval
    minutes = [0, 20, 40]
    current_min = int(dt.split(':')[1])
    distances = [abs(current_min - _min) for _min in minutes]
    closest_min = minutes[distances.index(min(distances))]
    current_time = dt.replace(':'+str(current_min), ':'+str(closest_min))
    current_time = datetime.datetime.strptime(current_time, "%Y/%m/%d %H:%M")

    return current_time


def st_prediction(boulderdf, selected_gym):
    # prediction for future
    s3.download_file(bucketname, modelname, modelname)
    model = pickle.load(open(modelname, "rb"))
    current_time = get_current_time()
    X_today = preprocess_current_data(boulderdf, selected_gym, current_time)
    prediction = int(model.predict(X_today)[0])
    # get time for next interval. round to the nearest 20min
    next_min = (current_time + (datetime.datetime.min - current_time) % datetime.timedelta(minutes=20)).strftime('%H:%M')
    st.markdown(f'**We predict the occupancy at {next_min} will be: {prediction}**\n')
    return


def st_avg_data(boulderdf, selected_gym):
    st.markdown(f"""
    ## Average data for {selected_gym}\n
    This plot shows the average occupancy, queue and weather for the given weekday.
    """)
    today = datetime.date.today()
    weekdays = [(today + datetime.timedelta(days=x)).strftime("%A") for x in range(7)]
    avg_day = st.radio('Select day of the week', weekdays)
    avgdf = avg_data_day(boulderdf, weekdays.index(avg_day), selected_gym)
    if avgdf.empty:
        st.error('There is no data to show at all. The gym might be closed for a long time')
    else:
        st.plotly_chart(plot_data(avgdf), width=800)
    return


if __name__ == "__main__":

    st.set_page_config(
        page_title="Bouldern",
        #layout="wide",
        page_icon="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/271/person-climbing_1f9d7.png")
    st.title('Boulder gym tracker')

    st.image('https://land8.com/wp-content/uploads/2017/07/Bouldering1.jpg', width=700)
    st.write("Github repo: [![Star](https://img.shields.io/github/stars/anebz/boulder.svg?logo=github&style=social)](https://gitHub.com/anebz/boulder)")

    s3.download_file(bucketname, dfname, dfname)
    boulderdf = pd.read_csv(dfname)

    selected_gym, selected_date = st_given_day(boulderdf)
    # only show prediction for current day
    #if str(selected_date) == str(datetime.datetime.today().strftime('%Y-%m-%d')):
    #    st_prediction(boulderdf, selected_gym)
    st_avg_data(boulderdf, selected_gym)

    st.markdown(f"""
    Does your gym show this occupancy data? Make a PR yourself or let us know and we'll add your gym 😎\n
    Created by [anebz](https://github.com/anebz) and [AnglinaBhambra](https://github.com/AnglinaBhambra).\n
    Follow us! [![@aberasategi](https://img.shields.io/twitter/follow/aberasategi?style=social)](https://www.twitter.com/aberasategi)
    [![@_AnglinaB](https://img.shields.io/twitter/follow/_AnglinaB?style=social)](https://www.twitter.com/_AnglinaB)""")

