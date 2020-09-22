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

To deploy to Scrapinghub:

```bash
cd /path/to/project/
shub deploy
```

gsutil cp boulder.csv gs://boulderbucket/

## Tools used

* [Scrapy for Python](https://scrapy.org/)
  * [Documentation](https://doc.scrapy.org/)
* [Scrapinghub](https://www.scrapinghub.com/scrapy-cloud/)
  * [Documentation](https://doc.scrapinghub.com/scrapy-cloud.html)
* [PyOWM](https://github.com/csparpa/pyowm)
  * Set `OWM_API` in settings, either settings.py in local or Spider settings in Scrapinghub
* [Google Cloud Platform](https://cloud.google.com/sdk/docs/install)
  * [Set up storage](https://cloud.google.com/storage/docs/reference/libraries): credentials, API key
  * [Upload objects](https://cloud.google.com/storage/docs/uploading-objects#gsutil). First needs to install `gsutil`.
    * `gsutil cp Desktop/kitten.png gs://boulderbucket`

## next tasks

* [~] [Save output differently](https://docs.scrapy.org/en/latest/topics/feed-exports.html#storages)
  * Check Pipelines in scrapy docs
  * https://console.cloud.google.com/storage/browser/boulderbucket
  * https://doc.scrapy.org/en/latest/topics/item-pipeline.html
  * https://stackoverflow.com/questions/55768694/getting-spider-on-scrapy-cloud-to-store-files-on-google-cloud-storage-using-gcsf
  * https://www.simoahava.com/google-cloud/scrape-domain-and-write-results-to-bigquery/
  * https://medium.com/@acowpy/scraping-files-images-using-scrapy-scrapinghub-and-google-cloud-storage-c7da9f9ac302
* [ ] Front end visualization

---------

## Resources

### Environment variables in Scrapinghub

1. Go to Spiders, click on your spider, raw settings and save your variable in this format
   1. `API = '123'`
2. Retrieve the environment variable in your code in this format
   1. `api = self.settings['API']`
   2. [How to access settings](https://doc.scrapy.org/en/latest/topics/settings.html)
3. Deploy the code, delete the periodic jobs, start it again.