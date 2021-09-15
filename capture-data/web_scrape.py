import os
import re
import json
import time
import boto3
import pyowm
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta


gyms = {
    'Munich East': {
        'url': 'https://www.boulderwelt-muenchen-ost.de',
        'location': 'Munich',
        'function': get_occupancy_boulderwelt
    },
    'Munich West': {
        'url': 'https://www.boulderwelt-muenchen-west.de',
        'location': 'Munich',
        'function': get_occupancy_boulderwelt
    },
    'Munich South': {
        'url': 'https://www.boulderwelt-muenchen-sued.de',
        'location': 'Munich',
        'function': get_occupancy_boulderwelt
    },
    'Frankfurt': {
        'url': 'https://www.boulderwelt-frankfurt.de',
        'location': 'Frankfurt',
        'function': get_occupancy_boulderwelt
    },
    'Dortmund': {
        'url': 'https://www.boulderwelt-dortmund.de',
        'location': 'Dortmund',
        'function': get_occupancy_boulderwelt
    },
    'Regensburg': {
        'url': 'https://www.boulderwelt-regensburg.de',
        'location': 'Regensburg',
        'function': get_occupancy_boulderwelt
    },
    'Magicmountain': {
        'url': 'https://www.magicmountain.de/preise',
        'location': 'Berlin',
        'function': get_occupancy_magicmountain
    },
    'Area85': {
        'url': 'https://www.area-85.de/klettern-berlin',
        'location': 'Berlin',
        'function': get_occupancy_area85
    },
}


def get_occupancy_boulderwelt(url: str) -> tuple():
    # make POST request to admin-ajax.php 
    req = requests.post(f"{url}/wp-admin/admin-ajax.php", data={"action": "cxo_get_crowd_indicator"})
    if req.status_code != 200:
        return 0, 0
    data = json.loads(req.text)
    occupancy, waiting = data['percent'], data['queue']
    return occupancy, waiting


def get_occupancy_magicmountain(url: str) -> tuple():
    page = requests.get(url)
    if page.status_code != 200:
        return 0, 0
    soup = BeautifulSoup(page.content, 'html.parser')
    page2 = requests.get(soup.find(id='idIframe')['src'])
    if page2.status_code != 200:
        return 0, 0
    
    soup2 = BeautifulSoup(page2.content, 'html.parser')
    occupancy = int(soup2.find('div', 'actcounter zoom')['data-value'])
    waiting = 0
    return occupancy, waiting


def get_occupancy_area85(url: str) -> tuple():
    page = requests.get(url)
    if page.status_code != 200:
        return 0, 0
    try:
        soup = BeautifulSoup(page.content, 'html.parser')
        occupancy = int(re.search(r'Trafficlight\("(\d+)"', str(soup.find(id='boxzilla-box-5540-content'))).group(1))
        waiting = 0
    except TypeError:
        occupancy, waiting = 0, 0
    return occupancy, waiting


def get_weather_info(location: str) -> tuple():
    '''
    Get weather temperature and status for a specific location in Germany
    '''
    temp = 0
    status = ''
    for i in range(5):
        try:
            mgr = pyowm.OWM(os.environ['OWM_API']).weather_manager()
            observation = mgr.weather_at_place(location).weather
            temp = round(observation.temperature('celsius')['temp'])
            status = observation.status
            break
        except:
            print(f"try i={i}/5. PYOWM gives timeout error at location: {location}")
        time.sleep(5)
    return temp, status


def scrape_websites() -> pd.DataFrame:

    webdata = []
    # Winter time: (datetime.now() + timedelta(hours=1)). Currently +2 because in summer time
    current_time = (datetime.now() + timedelta(hours=2)).strftime("%Y/%m/%d %H:%M")

    for gym_name, gym_data in gyms.items():
        weather_temp, weather_status = get_weather_info(gym_data['location'])
        occupancy, waiting = gym_data['function'](gym_data['url'])
        print(f"{gym_name}: occupancy={occupancy}, waiting={waiting}, temp={weather_temp}, status={weather_status}")
        if occupancy == 0 and waiting == 0:
            continue
        webdata.append((current_time, gym_name, occupancy, waiting, weather_temp, weather_status))
  
    webdf = pd.DataFrame(data=webdata, columns=['current_time', 'gym_name', 'occupancy', 'waiting', 'weather_temp', 'weather_status'])
    return webdf


def lambda_handler(event, context):
    webdf = scrape_websites()

    # only update if occupancy in gyms is > 0
    if webdf.empty:
        print("Nothing was scraped, S3 is not updated")
        return

    # download dataset from S3
    s3 = boto3.client('s3')
    dfpath = f"/tmp/{os.environ['CSVNAME']}"

    # download dataset from S3
    s3.download_file(os.environ['BUCKETNAME'], os.environ['CSVNAME'], dfpath)

    # merge boulderdata with tmp file
    webdf.append(pd.read_csv(dfpath)).to_csv(dfpath, index=False)
    s3.upload_file(dfpath, os.environ['BUCKETNAME'], os.environ['CSVNAME'])
    print("Scraping done and data updated to S3")
    return
