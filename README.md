# Boulder gym tracker project

https://app.scrapinghub.com/p/471449/jobs
shub deploy 471449

To run locally:

```bash
scrapy shell
cd /path/to/project/
scrapy crawl boulder -o output.json
```

## Tools used

* [Scrapy for Python](https://scrapy.org/)

## next tasks

* [Save weather](https://github.com/csparpa/pyowm)
* [Save output differently](https://docs.scrapy.org/en/latest/topics/feed-exports.html#storages) S3, GCP? because Items from Jobs don't last long in the free version
