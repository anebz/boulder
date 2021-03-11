import os
import boto3
import subprocess
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()
# it assumes that credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are already set as env variables
s3 = boto3.client('s3')
bucketname = 'bboulderdataset'
dfname = 'boulderdata.csv'

@sched.scheduled_job('cron', hour='7-23', minute='*/15')
def run_backend():
    # run scraping script in bash
    bashCommand = "scrapy crawl boulder -o output.csv"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print("Finished scraping")

    if os.path.isdir('output.csv'):
        # merge boulderdata with tmp file
        pd.read_csv('output.csv').append(pd.read_csv(dfname)).to_csv(dfname, index=False)
        os.remove('output.csv')

        # upload to AWS
        response = s3.upload_file(dfname, bucketname, dfname)
        print("Finished uploading")
    return

if __name__ == "__main__":
    # download dataset from S3
    s3.download_file(bucketname, dfname, dfname)
    sched.start()
