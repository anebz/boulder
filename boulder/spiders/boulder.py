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
        owm = pyowm.OWM(self.settings['OWM_API'])
        mgr = owm.weather_manager()
        observation = mgr.weather_at_place(location+',DE').weather
        weather_temp = observation.temperature('celsius')['temp']
        weather_status = observation.status
        return weather_temp, weather_status


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
        current_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        location = gym_name if gym_name not in ['ost', 'west'] else 'muenchen'
        weather_temp, weather_status = self.get_weather_info(location)

        occupancy, waiting = self.process_occupancy(response)

        yield {'Gym': gym_name, 'Date': current_time, 'Occupancy': occupancy, 'Waiting': waiting,
               'Temperature': weather_temp, 'Weather': weather_status}
