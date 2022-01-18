# Boulder gym tracker project

![ ](boulder.png)

## How to contribute

If you want to contribute, see the [issues](https://github.com/anebz/boulder/issues) and write a comment saying that you want to work on it. Additionally, if you think of a new issue, feel free to add it :)

## How to add a new gym

If you know a gym that shows the occupancy data, we can add it to the app!

We usually have a list of gyms to add in the [issues](https://github.com/anebz/boulder/issues) so if it's there, just write a comment saying which gym you would like to work on. If it's a new gym, then please follow these steps:

1. Fork the repo
2. Add gym information in `gymdata.json`
    * Gym name
    * Gym website URL
    * Gym location
    * Latitude
    * Longitude
    * Name of the function for scraping
3. In `capture-data/web_scrape.py`, add a new function with the name that you specified in the json before.
    * This function should take the `gym_name` (str) and `url` (str) as input
    * The function should return the occupancy number (int)
    * Make sure there's try/except so that the function doesn't crash!
4. Make a pull request
5. We will review it
6. Gym added 🏋️
