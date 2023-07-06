import datetime as dt

import scrapy

from music_data_scraper.items import BillboardItem
from music_data_scraper.itemloaders import BillboardItemLoader


class BillboardSpider(scrapy.Spider):
    
    # the starting and the ending dates for charts
    resp_date = dt.date(1958, 8, 2)
    ending_date = dt.date(2023, 5, 27)
    
    name = "billboard_spider"  # the spider name
    allowed_domains = ["billboard.com"]
    start_urls = ["https://www.billboard.com/charts/hot-100/" 
        + resp_date.strftime('%Y-%m-%d')]  # the url of the very first chart
    
    
    def parse(self, response):
        
        print('parsing', self.resp_date)  # for information only
        
        # grab the whole chart and its date
        hot100 = response.css('div.o-chart-results-list-row-container')
        hot_date = response.css('p.c-tagline.a-font-primary-medium-xs::text')\
            .get().replace('Week of ', '')
        hot_date = dt.datetime.strptime(hot_date, '%B %d, %Y').date()
        
        # scrap the 1st chart position
        hot1 = hot100[0]
        hot_stats = hot1.css('span.c-label.a-font-primary-bold-l::text')
        bb_item = BillboardItemLoader(item=BillboardItem(), selector=hot1)
        
        bb_item.add_value('date', hot_date)
        bb_item.add_value('pos', hot_stats[0].get())
        bb_item.add_css('artist', 'span.c-label.a-no-trucate::text')
        bb_item.add_css('song', 'h3::text')
        bb_item.add_value('last_week', hot_stats[1].get())
        bb_item.add_value('peak_pos', hot_stats[2].get())
        bb_item.add_value('wks_on_chart', hot_stats[3].get())
        
        yield bb_item.load_item()
        
        # scrap the 2nd-100th chart positions
        for hot in hot100[1:]:
            hot_stats = hot.css('span.c-label.a-font-primary-m::text')
            bb_item = BillboardItemLoader(item=BillboardItem(), selector=hot)
            
            bb_item.add_value('date', hot_date)
            bb_item.add_css('pos', 'span.c-label.a-font-primary-bold-l::text')
            bb_item.add_css('artist', 'span.c-label.a-no-trucate::text')
            bb_item.add_css('song', 'h3::text')
            bb_item.add_value('last_week', hot_stats[0].get())
            bb_item.add_value('peak_pos', hot_stats[1].get())
            bb_item.add_value('wks_on_chart', hot_stats[2].get())
            
            yield bb_item.load_item()
        
        # set new week
        self.resp_date = self.resp_date + dt.timedelta(weeks=1)
        
        # grab new chart
        if self.resp_date <= self.ending_date:
            next_url = "https://www.billboard.com/charts/hot-100/"\
                        + self.resp_date.strftime('%Y-%m-%d')
            yield response.follow(next_url, callback=self.parse)
