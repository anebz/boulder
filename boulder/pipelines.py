# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from scrapy.exceptions import DropItem

class BoulderPipeline:
    def process_item(self, item, spider):

        # generally all the gyms open around [7-23]
        # some gyms (Dortmund, Frankfurt, Regensburg) open later in the morning in some days
        beg_hour, end_hour = 7, 23
        accepted_mins = [0, 15, 30, 45]
        hour, minute = int(item['current_time'][-5:-3]), int(item['current_time'][-2:])

        if hour < beg_hour or hour > end_hour:
            raise DropItem(f"Incorrect time: hours should be between {beg_hour}:00 and {end_hour}:00")

        # the crawling time should be in the quarter, with a tolerance of +-2mins
        for acc_t in accepted_mins:
            if minute >= max(0, acc_t-2) and minute <= min(acc_t+2, 60):
                return item
        else:
            raise DropItem(f"Incorrect time: minutes should be in {', '.join(map(str, accepted_mins))}")
