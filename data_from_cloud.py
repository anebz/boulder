import os
import sys
import yaml
import pandas as pd
from tqdm import tqdm
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


def get_data_from_scrapinghub(project, spider, limit=-1):
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
            if job.metadata.get(u'close_reason') == u'finished':
                job_key_name = int(key.split('/')[2])

                # only to be used when data is already pre-loaded. Only load new items
                if limit != -1 and job_key_name <= limit:
                    return pd.DataFrame(data)
                for item in job.items.iter():
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
    df['key'] = df[b'_key']

    # only keep columns with converted names
    cols_to_keep = list(maps.keys())
    cols_to_keep.append('key')
    df = df[cols_to_keep]

    # decode b-string to tsring
    to_decode = ['gym_name', 'current_time', 'occupancy', 'weather_status', 'key']
    # https://stackoverflow.com/a/46696826/4569908
    for col in to_decode:
        df[col] = df[col].str.decode('utf-8')
    
    return df

if __name__ == "__main__":

    project, spider = get_spider_from_scrapinghub()
    try:
        # data has already been downloaded before
        prev_df = pd.read_csv('boulderdata.csv')
        # the csv is ordered chronologically, the first row is the latest job, with the most recent date
        latest_read_job = int(prev_df.loc[0]['key'].split('/')[2])
        new_df = get_data_from_scrapinghub(project, spider, limit=latest_read_job)
        new_df = parse_df(new_df)

        df = new_df.append(prev_df)
        df = df.drop('Unnamed: 0', axis=1)

    except FileNotFoundError:
        df = get_data_from_scrapinghub(project, spider)
        df = parse_df(df)

    df.to_csv('boulderdata.csv')
