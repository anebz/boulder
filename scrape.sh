#!/bin/bash
scrapy crawl boulder -o output.csv
python src/merge_df.py
aws s3 cp boulderdata.csv s3://bboulderdataset/boulderdata.csv