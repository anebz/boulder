import os
import re
import json
import time
import pytz
import boto3
import pyowm
import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup


def get_occupancy_boulderwelt(url: str) -> tuple():
    # make POST request to admin-ajax.php 
    req = requests.post(f"{url}/wp-admin/admin-ajax.php", data={"action": "cxo_get_crowd_indicator"})
    if req.status_code != 200:
        # admin-ajax.php not working
        page = requests.get(url)
        if page.status_code != 200:
            return 0, 0
        try:
            occupancy = round(float(re.search(r'style="margin-left:(.*?)%"', page.text).group(1)))
            waiting = 0
            return occupancy, waiting
        except:
            return 0, 0
    data = json.loads(req.text)
    # waiting system implemented
    if 'queue' in data:
        occupancy, waiting = data['percent'], data['queue']
    else:
        occupancy = data['level']
        waiting = 0
    return occupancy, waiting


def get_occupancy_magicmountain(url: str) -> tuple():
    request_url = 'https://www.boulderado.de/boulderadoweb/gym-clientcounter/index.php?mode=get&token=eyJhbGciOiJIUzI1NiIsICJ0eXAiOiJKV1QifQ.eyJjdXN0b21lciI6Ik1hZ2ljTW91bnRhaW4yMDIwMTQifQ.8919GglOcSMn9jl48zZVqNtZzXHh9RX23pN9F6DgX3E&ampel=1'
    page = requests.get(request_url)
    if page.status_code != 200:
        return 0, 0
    soup = BeautifulSoup(page.content, 'html.parser')
    try:
        occupancy = re.search(r'left: (\d*)%', str(soup.find_all("div", class_="pointer-image")[0]['style'])).group(1)
    except:
        occupancy = 0
    waiting = 0
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


def scrape_websites(current_time: str) -> pd.DataFrame:

    webdata = []
    for gym_name, gym_data in gyms.items():
        weather_temp, weather_status = get_weather_info(gym_data['location'])
        occupancy, waiting = gym_data['function'](gym_data['url'])
        print(f"{gym_name}: occupancy={occupancy}, waiting={waiting}, temp={weather_temp}, status={weather_status}")
        if occupancy == 0 and waiting == 0:
            continue
        webdata.append((current_time, gym_name, occupancy, waiting, weather_temp, weather_status))
  
    webdf = pd.DataFrame(data=webdata, columns=['time', 'gym_name', 'occupancy', 'waiting', 'weather_temp', 'weather_status'])
    return webdf


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
    'Berlin Magicmountain': {
        'url': 'https://www.magicmountain.de/preise',
        'location': 'Berlin',
        'function': get_occupancy_magicmountain
    }
}

def get_current_time():
    # https://stackoverflow.com/a/60169568/4569908
    dt = datetime.datetime.now()
    timeZone = pytz.timezone("Europe/Berlin")
    aware_dt = timeZone.localize(dt)
    if aware_dt.dst() != datetime.timedelta(0,0):
        #summer time
        dt += datetime.timedelta(hours=2)
    else:
        #winter time
        dt += datetime.timedelta(hours=1)
    dt = dt.strftime("%Y/%m/%d %H:%M")

    #round to the nearest 20min interval
    minutes = [0, 20, 40]
    current_min = int(dt.split(':')[1])
    distances = [abs(current_min - _min) for _min in minutes]
    closest_min = minutes[distances.index(min(distances))]
    current_time = dt.replace(':'+str(current_min), ':'+str(closest_min))

    return current_time


def lambda_handler(event, context):

    current_time = get_current_time()
    current_time_hh_mm = datetime.datetime.strptime(current_time, '%Y/%m/%d %H:%M').strftime("%H:%M")

    if current_time_hh_mm < '07:00' or current_time_hh_mm > '23:00':
        print("Scraping outside of opening hours, skipping")
        return
    
    print(f"Current time: {current_time}")

    webdf = scrape_websites(current_time)

    # only update if occupancy in gyms is > 0
    if webdf.empty:
        print("Nothing was scraped, S3 is not updated")
        return

    # download dataset from S3
    s3 = boto3.client('s3')
    dfpath = f"/tmp/{os.environ['CSVNAME']}"
    s3.download_file(os.environ['BUCKETNAME'], os.environ['CSVNAME'], dfpath)

    # merge boulderdata with tmp file
    webdf.append(pd.read_csv(dfpath)).to_csv(dfpath, index=False)

    # upload dataset to S3
    s3.upload_file(dfpath, os.environ['BUCKETNAME'], os.environ['CSVNAME'])
    print("Scraping done and data updated to S3")
    return
