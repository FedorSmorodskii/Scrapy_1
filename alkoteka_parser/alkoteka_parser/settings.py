BOT_NAME = 'alkoteka_parser'

SPIDER_MODULES = ['alkoteka_parser.spiders']
NEWSPIDER_MODULE = 'alkoteka_parser.spiders'

ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 2
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

USE_PROXY = True  # Флаг для включения/выключения прокси

PROXY_LIST = [
    'http://45.61.139.48:8000',
    'http://103.151.246.34:3128',
    'http://45.61.139.48:8000'
]

DOWNLOADER_MIDDLEWARES = {
    'alkoteka_parser.middlewares.RegionMiddleware': 100,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
}

if USE_PROXY:
    DOWNLOADER_MIDDLEWARES['alkoteka_parser.middlewares.ProxyMiddleware'] = 200
    DOWNLOADER_MIDDLEWARES['scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware'] = 110

ITEM_PIPELINES = {
    'alkoteka_parser.pipelines.AlkotekaParserPipeline': 300,
}

FEEDS = {
    'result.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': None,
        'indent': 4,
        'overwrite': True
    }
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 5

LOG_LEVEL = 'DEBUG'