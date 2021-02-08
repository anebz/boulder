import datetime
import pandas as pd
import streamlit as st
from src.average_data import avg_data_day, plot_ave_data

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
gyms = ['Munich East', 'Munich West', 'Dortmund', 'Frankfurt', 'Regensburg']
gyms_dict = {'Munich East': 'muenchen-ost', 'Munich West': 'muenchen-west', 'Dortmund': 'dortmund', 'Frankfurt': 'frankfurt', 'Regensburg': 'regensburg'}

if __name__ == "__main__":

    st.title('Boulder gym tracker')
    boulderdf = pd.read_csv("boulderdata.csv")

    gym = st.selectbox('Select gym', gyms)
    day = st.selectbox('Select day of the week', weekdays, index=datetime.datetime.today().weekday())

    avgdf = avg_data_day(boulderdf, weekdays.index(day), gyms_dict[gym])

    st.plotly_chart(plot_ave_data(avgdf))