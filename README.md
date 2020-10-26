# Boulder gym tracker project

To play around a website with scrapy:

```bash
scrapy shell
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

## Tools used

* [Scrapy for Python](https://scrapy.org/): [documentation](https://doc.scrapy.org/)
* [Scrapinghub](https://www.scrapinghub.com/scrapy-cloud/): [documentation](https://doc.scrapinghub.com/scrapy-cloud.html)
* [PyOWM](https://github.com/csparpa/pyowm)
  * Set `OWM_API` in settings, either settings.py in local or Spider settings in Scrapinghub
* [AWS S3](https://aws.amazon.com/s3/)
  * Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `FEED_URI = 's3://your-bucket/%(time)s.csv'` in settings as stated in the [documentation](https://doc.scrapy.org/en/latest/topics/feed-exports.html#s3)

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
