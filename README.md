# Boulder gym tracker project

To run crawler locally:

```bash
scrapy shell
cd /path/to/project/
scrapy crawl boulder -o output.json
```

To deploy to Scrapinghub:

```bash
cd /path/to/project/
shub deploy
```

## Tools used

* [Scrapy for Python](https://scrapy.org/)
  * [Documentation](https://doc.scrapy.org/)
* [Scrapinghub](https://www.scrapinghub.com/scrapy-cloud/)
  * [Documentation](https://doc.scrapinghub.com/scrapy-cloud.html)
* [PyOWM](https://github.com/csparpa/pyowm)

## next tasks

* [X] Weather integration with PyOWM
* [ ] [Save output differently](https://docs.scrapy.org/en/latest/topics/feed-exports.html#storages) S3, GCP? because Items from Jobs don't last long in the free version
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