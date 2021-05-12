import boto3
import datetime
import pandas as pd
import streamlit as st
from src.average_data import avg_data_day, plot_ave_data, given_day, plot_given_date

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
gyms = ['Munich East', 'Munich West', 'Munich South', 'Dortmund', 'Frankfurt', 'Regensburg']
gyms_dict = {'Munich East': 'muenchen-ost', 'Munich West': 'muenchen-west', 'Munich South': 'muenchen-sued', 
            'Dortmund': 'dortmund', 'Frankfurt': 'frankfurt', 'Regensburg': 'regensburg'}
bucketname = 'bboulderdataset'
dfname = 'boulderdata.csv'
today = datetime.date.today()
tomorrow = today + datetime.timedelta(days=1)
yesterday = today - datetime.timedelta(days=1)
first_date = datetime.date(2020, 9, 3)

if __name__ == "__main__":

    st.set_page_config(
        page_title="Bouldern", 
        page_icon="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/271/person-climbing_1f9d7.png")

    st.title('Boulder gym tracker')
    # it assumes that credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are already set as env variables
    boto3.client('s3').download_file(bucketname, dfname, dfname)
    boulderdf = pd.read_csv(dfname)

    gym = st.selectbox('Select gym', gyms)
    day = st.selectbox('Select day of the week', weekdays, index=datetime.datetime.today().weekday())

    avgdf = avg_data_day(boulderdf, weekdays.index(day), gyms_dict[gym])
    st.plotly_chart(plot_ave_data(avgdf))


    if st.button('Data Today'):
       # gym = st.selectbox('Select gym', gyms)
        givendaydf = given_day(boulderdf, str(today), gyms_dict[gym])
        st.plotly_chart(plot_given_date(givendaydf))


    # gym = st.selectbox('Select gym', gyms)
    selected_date = st.date_input('Selected date', yesterday)
    if selected_date < first_date:
        st.error('Error: End date must fall after 3rd September 2020.')
    elif selected_date > tomorrow:
        st.error('Error: Selected date must fall betweem 3rd September 2020 and now.')
    elif selected_date < tomorrow:
        st.success('Selected date: `%s`\n' % (selected_date))

    if selected_date < today:
        givendaydf = given_day(boulderdf, str(selected_date), gyms_dict[gym])
        st.plotly_chart(plot_given_date(givendaydf))

    st.markdown("Does your gym show how this occupancy data? Make a PR yourself or let us know and we'll add your gym 😎")
    st.markdown('Created by [anebz](https://github.com/anebz) and [AnglinaBhambra](https://github.com/AnglinaBhambra).')
