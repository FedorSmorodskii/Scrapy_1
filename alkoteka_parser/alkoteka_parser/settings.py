BOT_NAME = 'alkoteka_parser'

SPIDER_MODULES = ['alkoteka_parser.spiders']
NEWSPIDER_MODULE = 'alkoteka_parser.spiders'

ROBOTSTXT_OBEY = False

# Настройки из custom_settings паука можно перенести сюда
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 403, 404, 408, 429]
CONCURRENT_REQUESTS = 4
DOWNLOAD_DELAY = 1
LOG_LEVEL = 'INFO'

ITEM_PIPELINES = {
    'alkoteka_parser.pipelines.AlkotekaParserPipeline': 300,
}