import boto3
import datetime
import pandas as pd
import streamlit as st
from src.average_data import avg_data_day, plot_ave_data

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
gyms = ['Munich East', 'Munich West', 'Munich South', 'Dortmund', 'Frankfurt', 'Regensburg']
gyms_dict = {'Munich East': 'muenchen-ost', 'Munich West': 'muenchen-west', 'Munich South': 'muenchen-sued', 
            'Dortmund': 'dortmund', 'Frankfurt': 'frankfurt', 'Regensburg': 'regensburg'}
bucketname = 'bboulderdataset'
dfname = 'boulderdata.csv'

if __name__ == "__main__":

    # Set page title and favicon.
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

    st.markdown('Created by [anebz](https://github.com/anebz) and [AnglinaBhambra](https://github.com/AnglinaBhambra).')
