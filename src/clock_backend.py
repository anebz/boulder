import os
import boto3
import subprocess
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from web_scrape import scrape_websites

sched = BlockingScheduler()
# it assumes that credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are already set as env variables
s3 = boto3.client('s3')
bucketname = 'bboulderdataset'
dfname = 'boulderdata.csv'

@sched.scheduled_job('cron', hour='7-23', minute='*/15')
def run_backend():

    print("Scraping bouldering gyms")
    webdf = scrape_websites()

    # only update if occupancy in gyms is > 0
    if not (webdf['occupancy'] == 0).all():
        # merge boulderdata with tmp file
        webdf.append(pd.read_csv(dfname)).to_csv(dfname, index=False)
        # upload to AWS
        print("Updating the S3 dataset")
        response = s3.upload_file(dfname, bucketname, dfname)
    else:
        # all gyms are empty, don't do anything
        print("Nothing was scraped, S3 is not updated")
    print("Done")
    return


if __name__ == "__main__":
    # download dataset from S3
    s3.download_file(bucketname, dfname, dfname)
    sched.start()
