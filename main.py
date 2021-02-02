import pandas as pd
import streamlit as st
from src.average_data import avg_data_day, plot_ave_data

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
gyms = ['Munich East', 'Munich West', 'Regensburg', 'Dortmund', 'Frankfurt']
gyms_dict = {'Munich East': 'muenchen-ost', 'Munich West': 'muenchen-west', 'Regensburg': 'regensburg', 'Dortmund': 'dortmund', 'Frankfurt': 'frankfurt'}

if __name__ == "__main__":

    st.title('Boulder gym tracker')
    boulderdf = pd.read_csv("boulderdata.csv")

    gym = st.selectbox('Select gym', gyms)
    day = st.selectbox('Select day of the week', weekdays)

    ave_data = avg_data_day(boulderdf, weekdays.index(day), gyms_dict[gym])

    st.write("Plotting average occupancy, waiting people and weather")
    st.pyplot(plot_ave_data(ave_data))
