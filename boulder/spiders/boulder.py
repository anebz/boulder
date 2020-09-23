import re
import pyowm
import scrapy
import datetime

class Boulder(scrapy.Spider):
    name = 'boulder'
    start_urls = ['https://www.boulderwelt-muenchen-ost.de/',
                'https://www.boulderwelt-muenchen-west.de/',
                'https://www.boulderwelt-frankfurt.de/',
                'https://www.boulderwelt-dortmund.de/',
                'https://www.boulderwelt-regensburg.de/']


    def get_weather_info(self, location):
        '''
        Get weather temperature and status for a specific location in Germany
        '''
        location = location if 'muenchen' not in location else 'muenchen'

        owm = pyowm.OWM(self.settings['OWM_API'])
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(location+',DE').weather
        return observation.temperature('celsius')['temp'], observation.status


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
        Parameters:
        * Gym name
        * Current time
        * Occupancy of gym
        * Number of people waiting
        * Weather temperature
        * Weather status (clear, clouds, rain)
        '''
        item = {}
        item['gym_name'] = re.search("-([\w-]+)\..", response.url).group(1)
        item['current_time'] = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        item['occupancy'], item['waiting'] = self.process_occupancy(response)
        item['weather_temp'], item['weather_status'] = self.get_weather_info(item['gym_name'])

        yield item
