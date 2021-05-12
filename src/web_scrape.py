import os
import re
import sys
import time
import pyowm
import requests
import pandas as pd
from datetime import datetime, timedelta

urls = ['https://www.boulderwelt-muenchen-ost.de/',
        'https://www.boulderwelt-muenchen-west.de/',
        'https://www.boulderwelt-muenchen-sued.de/',
        'https://www.boulderwelt-frankfurt.de/',
        'https://www.boulderwelt-dortmund.de/',
        'https://www.boulderwelt-regensburg.de/']


def process_occupancy(resp: str) -> tuple():
    # extract occupancy percentage from html. When gyms are closed, the occupancy is ''
    occupancy = re.search(r'\<div style=".*?"\>(.*?)\<\/div\>', resp)
    try:
        occupancy = int(occupancy.group(1))
    except:
        occupancy = 0

    # due to COVID, if the gym reaches the corona capacity, people have to wait
    # this extracts how many people are waiting
    waiting = re.search(r"\<span\>(.*?)BOULDERER WARTEN\<\/span\>", resp)
    try:
        waiting = int(waiting.group(1))
    except:
        waiting = 0

    return occupancy, waiting


def get_weather_info(location: str) -> tuple():
    '''
    Get weather temperature and status for a specific location in Germany
    '''
    location = location if 'muenchen' not in location else 'muenchen'
    for i in range(5):
        try:
            mgr = pyowm.OWM(os.environ['OWM_API']).weather_manager()
            observation = mgr.weather_at_place(location+',DE').weather
            temp = observation.temperature('celsius')['temp']
            status = observation.status
            break
        except TimeoutError as ti:
            print(f"try i={i}/5. PYOWM gives timeout error at location: {location}")
            sys.stdout.flush()
        time.sleep(5)
    if not temp:
        temp = 0
    if not status:
        status = ''
    return temp, status


def scrape_websites() -> pd.DataFrame:

    webdata = []
    # Winter time: (datetime.now() + timedelta(hours=1))
    current_time = datetime.now().strftime("%Y/%m/%d %H:%M")
    for webpage in urls:
        gym_name = re.search("-([\w-]+)\.", webpage).group(1)
        weather_temp, weather_status = get_weather_info(gym_name)

        # scrape occupancy and waiting values from HTML response
        html_resp = requests.get(webpage).text
        occupancy, waiting = process_occupancy(html_resp)
        webdata.append((current_time, gym_name, occupancy, waiting, weather_temp, weather_status))

    webdf = pd.DataFrame(
            data=webdata, 
            columns=['current_time', 'gym_name', 'occupancy', 'waiting', 'weather_temp', 'weather_status'])
    return webdf
