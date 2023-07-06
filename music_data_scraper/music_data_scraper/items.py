import scrapy


class BillboardItem(scrapy.Item):
    date = scrapy.Field()
    pos = scrapy.Field()
    artist = scrapy.Field()
    song = scrapy.Field()
    last_week = scrapy.Field()
    peak_pos = scrapy.Field()
    wks_on_chart = scrapy.Field()
