# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from scrapy.exceptions import DropItem

class BoulderPipeline:
    def process_item(self, item, spider):
        item_time = int(item['current_time'][-2:])
        # the crawling time should be in the quarter, with a tolerance of +-2mins
        for acc_t in (0, 15, 30, 45):
            if item_time >= max(0, acc_t-2) and item_time <= min(acc_t+2, 60):
                return item
        else:
            raise DropItem("Incorrect time: minutes should be in 00, 15, 30, 45")

