import re
import scrapy
from datetime import datetime
from ..items import BoulderItem

class Boulder(scrapy.Spider):
    name = 'boulder'
    start_urls = ['https://www.boulderwelt-muenchen-ost.de/',
                  'https://www.boulderwelt-muenchen-west.de/',
                  'https://www.boulderwelt-frankfurt.de/',
                  'https://www.boulderwelt-dortmund.de/',
                  'https://www.boulderwelt-regensburg.de/']

    def parse(self, response):

        gym_name = re.search("-(\w+)\.", response.url).group(1)
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")

        crowdleveltag = response.css('div#crowd-level-tags-container')[0]

        # not crowded
        child = crowdleveltag.css('div.crowd-level-pointer')[0]
        text = child.css('div')[1].css('div')[0].css('div::text').get()
        occupancy = int(text[:-1])

        # crowded
        child = crowdleveltag.css('div.crowd-level-stop')[0]
        waiting = child.css('span::text').get()
        try:
            waiting = int(re.search(r'\d+', waiting).group())
        except:
            waiting = 0

        yield {'Gym': gym_name, 'Date': current_time, 'Occupancy': occupancy, 'Waiting': waiting}
