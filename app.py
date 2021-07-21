import os
import boto3
import pickle
import datetime
import pandas as pd
import streamlit as st
from src.visualize_data import avg_data_day, given_day, preprocess_current_data, plot_data

gyms = {'Munich East': 'muenchen-ost', 'Munich West': 'muenchen-west', 'Munich South': 'muenchen-sued', 
        'Dortmund': 'dortmund', 'Frankfurt': 'frankfurt', 'Regensburg': 'regensburg'}
bucketname = 'bboulderdataset'
dfname = 'boulderdata.csv'
modelname = 'model.dat'
s3 = boto3.client('s3')
s3_buffer = 1 # 1min

def st_given_day(boulderdf):
    # ask user for gym and date input
    st.markdown("""
    ## How full is my gym today?\n
    Due to Corona, gyms have reduced their capacity. Once the Corona capacity is reached, people have to wait to enter the gym.\n
    You can see the occupancy as a percentage of Corona capacity and the weather in the plot.\n
    If the occupancy is above 100%, that means the Corona capacity has been filled and people are waiting to enter the gym.
    """)
    selected_gym = st.selectbox('Select gym', gyms.keys())
    today = datetime.date.today()
    # get first available date, the last row in the dataframe
    first_date = datetime.datetime.strptime(boulderdf.iloc[-1]['current_time'], "%Y/%m/%d %H:%M")
    selected_date = st.date_input('Selected date', today, min_value=first_date, max_value=today)

    # display the data for the given day
    givendaydf = given_day(boulderdf, str(selected_date), gyms[selected_gym])
    if givendaydf.empty:
        st.error('There is no data to show for this day. The gym might be closed')
    else:
        st.plotly_chart(plot_data(givendaydf))
    return selected_gym


def st_prediction(boulderdf, selected_gym):
    # prediction for future
    if not os.path.isfile(modelname):
        s3.download_file(bucketname, modelname, modelname)
    model = pickle.load(open(modelname, "rb"))
    current_time = datetime.datetime.now()
    X_today = preprocess_current_data(boulderdf, gyms, selected_gym, current_time)
    prediction = round(model.predict(X_today)[0])
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
    avg_day = st.selectbox('Select day of the week', weekdays)
    avgdf = avg_data_day(boulderdf, weekdays.index(avg_day), gyms[selected_gym])
    if avgdf.empty:
        st.error('There is no data to show at all. The gym might be closed for a long time')
    else:
        st.plotly_chart(plot_data(avgdf))
    return


if __name__ == "__main__":

    st.set_page_config(
        page_title="Bouldern",
        page_icon="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/271/person-climbing_1f9d7.png")
    st.title('Boulder gym tracker')

    s3.download_file(bucketname, dfname, dfname)
    boulderdf = pd.read_csv(dfname)

    selected_gym = st_given_day(boulderdf)
    st_prediction(boulderdf, selected_gym)
    st_avg_data(boulderdf, selected_gym)

    st.markdown("Does your gym show how this occupancy data? Make a PR yourself or let us know and we'll add your gym 😎")
    st.markdown('Created by [anebz](https://github.com/anebz) and [AnglinaBhambra](https://github.com/AnglinaBhambra).')
