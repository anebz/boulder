import os
import pytz
import boto3
import pickle
import datetime
import pandas as pd
import streamlit as st
import streamlit_analytics
from src.visualize_data import avg_data_day, given_day, preprocess_current_data, plot_data

bucketname = 'bboulderdataset'
dfname = 'boulderdata.csv'
modelname = 'model.dat'
gymdataname = 'gymdata.json'
s3 = boto3.client('s3')

def st_given_day(boulderdf, gymdatadf):
    # ask user for gym and date input
    st.markdown("""
    ## How full is my gym today?\n
    Due to Corona, gyms have reduced their capacity. If the occupancy is above 100%, that means people are waiting to enter the gym.
    """)

    selected_gym = st.radio('Select a gym', sorted(list(boulderdf['gym_name'].unique())))
    today = datetime.date.today()
    # get first available date, the last row in the dataframe
    first_date = datetime.datetime.strptime(boulderdf.iloc[-1]['time'], "%Y/%m/%d %H:%M")
    selected_date = st.date_input('Selected date', today, min_value=first_date, max_value=today)

    st.markdown(f"### Showing results for [{selected_gym}]({gymdatadf[selected_gym]['url']})\nOccupancy shown in percentage")

    # display the data for the given day
    givendaydf = given_day(boulderdf, str(selected_date), selected_gym)
    if givendaydf.empty:
        st.error('There is no data to show for this day. The gym might be closed')
    else:
        st.altair_chart(plot_data(givendaydf), use_container_width=True)
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
        st.altair_chart(plot_data(avgdf), use_container_width=True)
    return


if __name__ == "__main__":

    st.set_page_config(
        page_title="Bouldern",
        #layout="wide",
        page_icon="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/271/person-climbing_1f9d7.png")
    st.title('Boulder gym tracker')
    st.markdown('**Update 30.12.2021: currently supporting 15 gyms!** 🚀')
    st.write("Github repo: [![Star](https://img.shields.io/github/stars/anebz/boulder.svg?logo=github&style=social)](https://gitHub.com/anebz/boulder)")
    st.image('https://land8.com/wp-content/uploads/2017/07/Bouldering1.jpg', width=700)

    s3.download_file(bucketname, gymdataname, gymdataname)
    gymdatadf = pd.read_json(gymdataname)

    # plot map with gym coordinates
    st.map(pd.DataFrame([[gymdatadf[gym_name]['lat'], gymdatadf[gym_name]['long']] for gym_name in gymdatadf], columns=['lat', 'lon']))

    # set up analytics
    if not os.path.isfile('firestore-key.json'):
        s3.download_file(bucketname, 'firestore-key.json', 'firestore-key.json')
    streamlit_analytics.start_tracking(firestore_key_file="firestore-key.json", firestore_collection_name="counts")

    s3.download_file(bucketname, dfname, dfname)
    boulderdf = pd.read_csv(dfname)

    selected_gym, selected_date = st_given_day(boulderdf, gymdatadf)
    # only show prediction for current day
    #if str(selected_date) == str(datetime.datetime.today().strftime('%Y-%m-%d')):
    #    st_prediction(boulderdf, selected_gym)
    st_avg_data(boulderdf, selected_gym)

    st.markdown(f"""
    Does your gym show this occupancy data? Make a PR yourself or let us know and we'll add your gym 😎\n
    Created by [anebz](https://github.com/anebz) and [AnglinaBhambra](https://github.com/AnglinaBhambra).\n
    Follow us! [![@anebzt](https://img.shields.io/twitter/follow/anebzt?style=social)](https://www.twitter.com/anebzt)
    [![@_AnglinaB](https://img.shields.io/twitter/follow/_AnglinaB?style=social)](https://www.twitter.com/_AnglinaB)""")
    streamlit_analytics.stop_tracking(firestore_key_file="firestore-key.json", firestore_collection_name="counts")
