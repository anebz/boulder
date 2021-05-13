import os
import re
import sys
import json
import time
import boto3
import pyowm
import requests
import pandas as pd
from io import StringIO
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
    for i in range(5):
        try:
            mgr = pyowm.OWM(os.environ['OWM_API']).weather_manager()
            observation = mgr.weather_at_place(location+',DE').weather
            temp = observation.temperature('celsius')['temp']
            status = observation.status
            break
        except:
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
    # +2 because Heroku time is 2h less than German time
    current_time = (datetime.now() + timedelta(hours=2)).strftime("%Y/%m/%d %H:%M")
    for url in urls:
        gym_name = re.search("-([\w-]+)\.", url).group(1)
        print(f"{gym_name}: getting weather info")
        weather_temp, weather_status = get_weather_info(gym_name)

        # scrape occupancy and waiting values from HTML response
        print(f"{gym_name}: getting occupancy info")
        occupancy, waiting = process_occupancy(url)
        if occupancy == 0 or waiting == 0:
            continue
        webdata.append((current_time, gym_name, occupancy, waiting, weather_temp, weather_status))

    webdf = pd.DataFrame(
            data=webdata,
            columns=['current_time', 'gym_name', 'occupancy', 'waiting', 'weather_temp', 'weather_status'])
    return webdf


def lambda_handler(event, context):
    print("Scraping websites")
    sys.stdout.flush()
    webdf = scrape_websites()

    # only update if occupancy in gyms is > 0
    if (webdf['occupancy'] == 0).all():
        print("Nothing was scraped, S3 is not updated")
        sys.stdout.flush()
        return

    # download dataset from S3
    s3 = boto3.client('s3')
    bucketname = 'bboulderdataset'
    dfname = 'boulderdata.csv'
    #s3.download_file(bucketname, dfname, dfname)
    csv_obj = s3.get_object(Bucket=bucketname, Key=dfname)
    csv_string = csv_obj['Body'].read().decode('utf-8')
    s3df = pd.read_csv(StringIO(csv_string))

    # merge boulderdata with tmp file
    webdf.append(s3df)

    csv_buf = StringIO()
    webdf.to_csv(csv_buf, header=True, index=False)
    csv_buf.seek(0)
    s3.put_object(Bucket=bucketname, Body=csv_buf.getvalue(), Key=dfname)
    #s3.upload_file(dfname, bucketname, dfname)
    print("Scraping done and data updated to S3")
    sys.stdout.flush()
    return