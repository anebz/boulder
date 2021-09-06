import os
import re
import json
import time
import boto3
import pyowm
from bs4 import BeautifulSoup
import requests
import pandas as pd
from datetime import datetime, timedelta

urls = ['https://www.boulderwelt-muenchen-ost.de/',
        'https://www.boulderwelt-muenchen-west.de/',
        'https://www.boulderwelt-muenchen-sued.de/',
        'https://www.boulderwelt-frankfurt.de/',
        'https://www.boulderwelt-dortmund.de/',
        'https://www.boulderwelt-regensburg.de/']

url_berlinMagicMountain = 'https://www.magicmountain.de/preise/#Besucheranzahl'
url_berlin_Area85 = 'https://www.area-85.de/klettern-berlin/'

def process_occupancy(url: str) -> tuple():
    # make POST request to admin-ajax.php 
    req = requests.post(f"{url}/wp-admin/admin-ajax.php", data = {"action": "cxo_get_crowd_indicator"})
    if req.status_code == 200:
        data = json.loads(req.text)
        print(data)
        occupancy = data['percent']
        waiting = data['queue']
    else:
        occupancy = 0
        waiting = 0
    return occupancy, waiting

def process_occupancy_berlinMagicMountain(url: str) -> tuple():
    #use beautiful soup to get the occupancy
    page = requests.get(url)
    if page.status_code == 200:
        soup = BeautifulSoup(page.content, 'html.parser')
        try:
            p1 = soup.find(id = 'idIframe')['src']
            page2 = requests.get(p1)
            if page2.status_code == 200:
                soup2 = BeautifulSoup(page2.content, 'html.parser')
                occupancy = int(soup2.find('div',
                                           'actcounter zoom')['data-value'])
            else:
                occupancy = 0
        except TypeError:
            occupancy = 0
                
    else:
        occupancy = 0
    waiting = 0
    return occupancy, waiting

def process_occupancy_area85(url: str) -> tuple():
    page = requests.get(url)
    if page.status_code == 200:
        try:
            soup = BeautifulSoup(page.content, 'html.parser')
            h = soup.find(id = 'boxzilla-box-5540-content')
            with_numbers = str(h.find_all('script')[1])
            occupancy = re.findall(r'\d+',
                                   with_numbers)[0]
            waiting = 0
        except TypeError:
            occupancy = 0
            waiting = 0
    return int(occupancy), waiting

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
            temp = round(observation.temperature('celsius')['temp'])
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
    for berlin_url, berlin_getter in zip([url_berlinMagicMountain, url_berlin_Area85], 
                                         [process_occupancy_berlinMagicMountain, process_occupancy_berlinMagicMountain]):
        gym_name = berlin_url.split('.')[1]
        weather_temp, weather_status = get_weather_info('berlin')
        #scrape occupancy (waiting 0 as not provided) from html
        occupancy,waiting = berlin_getter(berlin_url)
        print(f"{gym_name}: occupancy={occupancy}, waiting={waiting}, temp={weather_temp}, status={weather_status}")
        if occupancy == 0 and waiting == 0.:
            continue
        webdata.append((current_time, gym_name, occupancy, waiting, weather_temp, weather_status))      
    webdf = pd.DataFrame(data = webdata,
            columns = ['current_time', 'gym_name', 'occupancy', 'waiting', 'weather_temp', 'weather_status'])
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


