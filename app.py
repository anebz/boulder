import boto3
import datetime
import pandas as pd
import streamlit as st
from src.visualize_data import avg_data_day, plot_data, given_day

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
gyms = ['Munich East', 'Munich West', 'Munich South', 'Dortmund', 'Frankfurt', 'Regensburg']
gyms_dict = {'Munich East': 'muenchen-ost', 'Munich West': 'muenchen-west', 'Munich South': 'muenchen-sued', 
            'Dortmund': 'dortmund', 'Frankfurt': 'frankfurt', 'Regensburg': 'regensburg'}
bucketname = 'bboulderdataset'
dfname = 'boulderdata.csv'

if __name__ == "__main__":

    st.set_page_config(
        page_title="Bouldern",
        page_icon="https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/apple/271/person-climbing_1f9d7.png")

    st.title('Boulder gym tracker')
    # it assumes that credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are already set as env variables
    boto3.client('s3').download_file(bucketname, dfname, dfname)
    boulderdf = pd.read_csv(dfname)

    today = datetime.date.today()
    # get first available date, the last row in the dataframe
    first_date = datetime.datetime.strptime(boulderdf.iloc[-1]['current_time'], "%Y/%m/%d %H:%M")

    # ask user for gym and date input
    st.markdown("""
    ## How full is my gym today?\n
    Currently only the Munich and Frankfurt gyms are open. But Frankfurt is following a Click & Climb system and not showing the occupancy data.
    Therefore, for now we can only show data for the 3 Munich gyms.\n
    Due to Corona, gyms have reduced their capacity. Once the Corona capacity is reached, people have to wait to enter the gym.\n
    You can see the occupancy as a percentage of Corona capacity, the people in the queue and the weather in the plot.
    """)
    gym = st.selectbox('Select gym', gyms)
    selected_date = st.date_input('Selected date', today, min_value=first_date, max_value=today)

    # display the data for the given day
    givendaydf = given_day(boulderdf, str(selected_date), gyms_dict[gym])
    if givendaydf.empty:
        st.error('There is no data to show for this day. The gym might be closed')
    else:
        st.plotly_chart(plot_data(givendaydf), use_container_width=True)

    st.markdown(f"""
    ## Average data for {gym}\n
    This plot shows the average occupancy, queue and weather for the given weekday.
    """)
    avg_day = st.selectbox('Select day of the week', weekdays, index=today.weekday())
    avgdf = avg_data_day(boulderdf, weekdays.index(avg_day), gyms_dict[gym])
    if avgdf.empty:
        st.error('There is no data to show at all. The gym might be closed for a long time')
    else:
        st.plotly_chart(plot_data(avgdf), use_container_width=True)

    st.markdown("Does your gym show how this occupancy data? Make a PR yourself or let us know and we'll add your gym 😎")
    st.markdown('Created by [anebz](https://github.com/anebz) and [AnglinaBhambra](https://github.com/AnglinaBhambra).')
