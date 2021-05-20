import os
import re
import json
import time
import boto3
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


def process_occupancy(url: str) -> tuple():
    # make POST request to admin-ajax.php 
    req = requests.post(f"{url}/wp-admin/admin-ajax.php", data={"action": "cxo_get_crowd_indicator"})
    if req.status_code == 200:
        data = json.loads(req.text)
        occupancy = data['percent']
        waiting = data['queue']
    else:
        occupancy = 0
        waiting = 0
    return occupancy, waiting


def get_weather_info(location: str) -> tuple():
    '''
    Get weather temperature and status for a specific location in Germany
    '''
    location = location if 'muenchen' not in location else 'muenchen'
    temp = 0
    status = ''
    for i in range(5):
        try:
            mgr = pyowm.OWM(os.environ['OWM_API']).weather_manager()
            observation = mgr.weather_at_place(location+',DE').weather
            temp = observation.temperature('celsius')['temp']
            status = observation.status
            break
        except:
            print(f"try i={i}/5. PYOWM gives timeout error at location: {location}")
        time.sleep(5)
    return temp, status

def scrape_websites() -> pd.DataFrame:

    webdata = []
    # Winter time: (datetime.now() + timedelta(hours=1))
    # +2 because server time is UTC
    current_time = (datetime.now() + timedelta(hours=2)).strftime("%Y/%m/%d %H:%M")
    for url in urls:
        gym_name = re.search("-([\w-]+)\.", url).group(1)
        weather_temp, weather_status = get_weather_info(gym_name)

        # scrape occupancy and waiting values from HTML response
        occupancy, waiting = process_occupancy(url)
        print(f"{gym_name}: occupancy={occupancy}, waiting={waiting}, temp={weather_temp}, status={weather_status}")
        if occupancy == 0 and waiting == 0:
            continue
        webdata.append((current_time, gym_name, occupancy, waiting, weather_temp, weather_status))

    webdf = pd.DataFrame(data=webdata,
            columns=['current_time', 'gym_name', 'occupancy', 'waiting', 'weather_temp', 'weather_status'])
    return webdf


def lambda_handler(event, context):
    webdf = scrape_websites()

    # only update if occupancy in gyms is > 0
    if webdf.empty:
        print("Nothing was scraped, S3 is not updated")
        return

    # download dataset from S3
    s3 = boto3.client('s3')
    dfname = os.environ['CSVNAME']
    dfpath = f"/tmp/{os.environ['CSVNAME']}"

    # download dataset from S3
    s3.download_file(os.environ['BUCKETNAME'], dfname, dfpath)

    # merge boulderdata with tmp file
    webdf.append(pd.read_csv(dfpath)).to_csv(dfpath, index=False)
    s3.upload_file(dfpath, os.environ['BUCKETNAME'], dfname)

    print("Scraping done and data updated to S3")
    return