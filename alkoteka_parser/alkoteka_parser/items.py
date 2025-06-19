import scrapy

class AlkotekaProductItem(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    prev_price = scrapy.Field()
    available = scrapy.Field()
    region = scrapy.Field()
    url = scrapy.Field()
    # Добавьте другие поля по необходимости