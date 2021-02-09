import os
import sys
import glob
import json
import yaml
import boto3
import numpy as np
import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta
from scrapinghub import ScrapinghubClient


def get_spider_from_scrapinghub():
    # Scrapinghub API should be defined in the environment variables of the OS
    try:
        apikey = os.environ.get('SCRAPINGHUB_API')
    except:
        sys.exit('Scrapinghub API is not set in the environment variables')

    client = ScrapinghubClient(apikey)
    # obtain project_id from the 'project' parameter in 'scrapinghub.yml'
    project_id = yaml.load(open('scrapinghub.yml', 'r'), Loader=yaml.FullLoader)['project']

    project = client.get_project(project_id)
    # this project only contains one spider, that's why the first spider in the list is taken
    spider = project.spiders.get(project.spiders.list()[0]['id'])
    return project, spider


def download_from_s3():
    # it assumes that credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are already set as env variables
    client = boto3.client('s3')
    bucketname = 'bboulder'

    # bucket is empty
    if 'Contents' not in client.list_objects(Bucket=bucketname):
        print("No new data to retrieve from AWS S3")
        return
    
    # download each file into 'awsdata' folder and delete object from bucket
    for s3_key in tqdm(client.list_objects(Bucket=bucketname)['Contents']):
        s3_object = s3_key['Key']
        client.download_file(bucketname, s3_object, 'awsdata/'+s3_object)
        client.delete_object(Bucket=bucketname, Key=s3_object)
    return


def parse_aws_data(df):
    # access csvs downloaded from AWS S3 ordered by the earliest date
    os.chdir('awsdata')
    for infile in sorted(glob.glob('*.csv')):
        # change date format
        date = datetime.strptime(infile.strip('.csv'), '%Y-%m-%dT%H-%M-%S').strftime('%Y/%m/%d %H:%M')
        # add 1h for Berlin time
        date = (datetime.strptime(date, '%Y/%m/%d %H:%M') + timedelta(hours=1)).strftime('%Y/%m/%d %H:%M')

        # date is already in the df, duplicated data. skip
        if len(df[df['current_time'] == date]) > 0:
            continue

        # open and parse files downloaded from AWS S3
        with open(infile) as f:
            new_df = pd.DataFrame([json.loads(line.strip('\n')) for line in f.readlines()])
        if not new_df.empty:
            df = new_df.append(df)
        os.remove(infile)
    return df


def get_data_from_scrapinghub(project, spider, limit=''):
    data = []
    idx = 0
    while True:
        # Generate all job keys
        job_keys = [j['key'] for j in spider.jobs.iter(start=idx)]

        # all jobs have been inspected
        if len(job_keys) < 1:
            break

        # iterate all jobs, check only finished jobs, and append each item to the data
        for key in tqdm(job_keys, desc=str(idx)):
            job = project.jobs.get(key)
            if job.metadata.get(u'close_reason') != u'finished':
                continue
            for item in job.items.iter():
                # only to be used when data is already pre-loaded. Only load new items
                if limit != '' and item[b'current_time'].decode('utf-8') <= limit:
                    return pd.DataFrame(data)
                data.append(item)

        # https://python-scrapinghub.readthedocs.io/en/latest/client/apidocs.html#scrapinghub.client.jobs.Jobs.iter
        # Scrapinghub API only allows 1000 jobs to be loaded at each time
        idx += 1000
    return pd.DataFrame(data)


def parse_df(df):
    maps = {'gym_name': 'Gym', 'current_time': 'Date',
            'occupancy': 'Occupancy', 'waiting': 'Waiting',
            'weather_temp': 'Temperature', 'weather_status': 'Weather'}

    # map the old column names (Gym, Date, etc.) to new ones (gym_name, current_time, etc.)
    if b'Gym' in list(df):
        for k, v in maps.items():
            # https://stackoverflow.com/questions/53389699/pandas-dataframe-copy-the-contents-of-a-column-if-it-is-empty
            df[k] = np.where(df[k.encode('utf-8')].isnull(), df[v.encode('utf-8')], df[k.encode('utf-8')])
    else:
        for col in list(df):
            df[col.decode('utf-8')] = df[col]

    # only keep columns with converted names
    cols_to_keep = list(maps.keys())
    df = df[cols_to_keep]

    # decode b-string to string
    to_decode = ['gym_name', 'current_time', 'weather_status']
    # https://stackoverflow.com/a/46696826/4569908
    for col in to_decode:
        df[col] = df[col].str.decode('utf-8')
    
    return df


if __name__ == "__main__":

    os.makedirs("awsdata", exist_ok=True)
    try:
        prev_df = pd.read_csv('boulderdata.csv')
    except FileNotFoundError:
        df = get_data_from_scrapinghub(project, spider)
        df = parse_df(df)
        df.to_csv('boulderdata.csv', index=False)
        sys.exit()

    mode = 'aws'  # aws, scrapinghub
    if mode == 'aws':
        download_from_s3()
        df = parse_aws_data(prev_df)
        os.chdir('..')
    else:
        project, spider = get_spider_from_scrapinghub()
        # the csv is ordered chronologically, the first row is the latest job, with the most recent date
        latest_read_job = prev_df.loc[0]['current_time']
        new_df = get_data_from_scrapinghub(project, spider, limit=latest_read_job)

        if new_df.empty:
            print("No new jobs found")
            sys.exit()

        new_df = parse_df(new_df)
        df = new_df.append(prev_df)
        
    df.to_csv('boulderdata.csv', index=False)
