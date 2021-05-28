# Boulder gym tracker project

![ ](boulder.png)

## Backend Lambda

Set up the [serverless](https://www.serverless.com/framework/docs/getting-started/) directory. This requires AWS credentials.

```bash
cd capture_data/
sls --verbose
sls plugin install -n serverless-python-requirements
```

Deploy and invoke the Lambda function.

```bash
serverless deploy
serverless invoke -f s3tos3 --log
```

## Front-end

```python
pip install -r requirements.txt
```

Run [Streamlit](https://streamlit.io/) locally:

```bash
streamlit run app.py
```

### Front-end deployment: [Heroku](https://devcenter.heroku.com/)

1. Create app in Heroku and set a name. In this case, **`bouldern`**.
2. Create `Dockerfile` with [specific streamlit commands](https://discuss.streamlit.io/t/how-to-use-streamlit-in-docker/1067/2)
3. Set web and backend in `heroku.yml`
4. Create environment variables in Heroku: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `OWM_API` from [PyOWM](https://github.com/csparpa/pyowm)

Log in to Heroku from the terminal

```bash
# attach project to heroku app
heroku git:remote -a bouldern
# log in with the CLI. docker must be running
heroku container:login
```

Push and release project in Heroku

```bash
# push changes to heroku
heroku container:push web
# release app
heroku container:release web
# check logs
heroku logs --tail
```

Alternatively, as the way it's set up now, you can connect Heroku to Github so that the commits to the main branch trigger a Heroku deployment.

---------

## Resources

Legal info about scraping/crawling

1. [Web Scraping and Crawling Are Perfectly Legal, Right?](https://benbernardblog.com/web-scraping-and-crawling-are-perfectly-legal-right/)
2. [robots.txt file](https://www.boulderwelt-muenchen-ost.de/robots.txt) doesn't prohibit scraping the main webpage
3. No prohibitions in AGB or Datenschutzerklärung. No Nutzunsbedingungen

Estimation of circa 300 people for 59% of whole capacity (corona capacity).
