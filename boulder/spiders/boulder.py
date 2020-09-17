import re
import scrapy
from datetime import datetime

class Boulder(scrapy.Spider):
    name = 'boulder'
    start_urls = ['https://www.boulderwelt-muenchen-ost.de/',
                'https://www.boulderwelt-muenchen-west.de/',
                'https://www.boulderwelt-frankfurt.de/',
                'https://www.boulderwelt-dortmund.de/',
                'https://www.boulderwelt-regensburg.de/']

    def process_occupancy(self, response):
        '''
        Extract occupancy of gym and if full, number of people waiting
        '''

        crowdleveltag = response.css('div#crowd-level-tags-container')[0]
        # not crowded
        child = crowdleveltag.css('div.crowd-level-pointer')[0]
        text = child.css('div')[1].css('div')[0].css('div::text').get()
        try:
            occupancy = int(text[:-1])
        except:
            occupancy = 0

        # crowded
        child = crowdleveltag.css('div.crowd-level-stop')[0]
        waiting = child.css('span::text').get()
        try:
            waiting = int(re.search(r'\d+', waiting).group())
        except:
            waiting = 0
        
        return occupancy, waiting


    def parse(self, response):
        '''
        Function that the scrapy crawler calls, with the response of the URL provided in start_urls
        '''
        gym_name = re.search("-(\w+)\.", response.url).group(1)
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")


        occupancy, waiting = self.process_occupancy(response)

        yield {'Gym': gym_name, 'Date': current_time, 'Occupancy': occupancy, 'Waiting': waiting}
