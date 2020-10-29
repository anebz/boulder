# Boulder gym tracker project

Requirements for this project

```txt
boto
pyowm
PyYAML
scrapinghub
```

To play around a website with scrapy:

```bash
scrapy shell https://www.website.com
```

To run crawler locally and save item into `output.json`:

```bash
cd /path/to/project/
scrapy crawl boulder -o output.json
```

If an external storage is defined (S3 from AWS for example):

```bash
cd /path/to/project/
scrapy crawl boulder
```

To deploy to Scrapinghub:

```bash
cd /path/to/project/
shub deploy
```

Download items from AWS bucket. First, install `awscli` and configure your credentials

```bash
pip install awscli
aws configure
```

Enter the security credentials created in [AWS console](https://console.aws.amazon.com), click on your username at the top right, `My security credentials`, `Create new access key`. Enter your region as well. For me it's `eu-central-1`. Once this is done, to download to a specific folder, where `bboulder` is the bucket name in your AWS S3 account.

```bash
cd /path/to/project/
mkdir awsdata
cd awsdata
aws s3 sync s3://bboulder .
```

Run `streamlit` script:

```bash
streamlit run your-file.py
```

## Tools used

* [Scrapy for Python](https://scrapy.org/): [documentation](https://doc.scrapy.org/)
* [Scrapinghub](https://www.scrapinghub.com/scrapy-cloud/): [documentation](https://doc.scrapinghub.com/scrapy-cloud.html)
* [PyOWM](https://github.com/csparpa/pyowm)
  * Set `OWM_API` in settings, either settings.py in local or Spider settings in Scrapinghub
* [AWS S3](https://aws.amazon.com/s3/)
  * Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `FEED_URI = 's3://your-bucket/%(time)s.csv'` in settings as stated in the [documentation](https://doc.scrapy.org/en/latest/topics/feed-exports.html#s3)
* [Streamlit](https://streamlit.io/)

---------

## Resources

### Environment variables in Scrapinghub

1. Go to Spiders, click on your spider, raw settings and save your variable in this format
   1. `API = '123'`
2. Retrieve the environment variable in your code in this format
   1. `api = self.settings['API']`
   2. [How to access settings](https://doc.scrapy.org/en/latest/topics/settings.html)
3. Deploy the code, delete the periodic jobs, start it again

### Legal info about scraping/crawling

1. [Web Scraping and Crawling Are Perfectly Legal, Right?](https://benbernardblog.com/web-scraping-and-crawling-are-perfectly-legal-right/)
2. [robots.txt file](https://www.boulderwelt-muenchen-ost.de/robots.txt) doesn't disallow scraping the main webpage.
3. No prohibitions in AGB or Datenschutzerklärung. No Nutzunsbedingungen

---

Estimation of circa 300 people for 59% of whole capacity (corona capacity).
