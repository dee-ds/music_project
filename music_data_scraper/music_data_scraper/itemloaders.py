from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst, MapCompose


class BillboardItemLoader(ItemLoader):

    default_output_processor = TakeFirst()
    
    st = str.strip
    
    pos_in = MapCompose(st, int)
    artist_in = MapCompose(st)
    song_in = MapCompose(st)
    last_week_in = MapCompose(
        st, lambda x: int(x) if x != '-' else float("NaN")
    )
    peak_pos_in = MapCompose(st, int)
    wks_on_chart_in = MapCompose(st, int)
