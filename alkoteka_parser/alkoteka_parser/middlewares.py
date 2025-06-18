import random
from urllib.parse import urlparse
from scrapy import signals
from scrapy.exceptions import NotConfigured


class ProxyMiddleware:
    def __init__(self, proxy_list):
        self.proxy_list = proxy_list

    @classmethod
    def from_crawler(cls, crawler):
        # Проверяем, включены ли прокси в настройках
        if not crawler.settings.getbool('USE_PROXY'):
            raise NotConfigured('Proxy middleware disabled by settings')

        proxy_list = crawler.settings.getlist('PROXY_LIST', [])
        if not proxy_list:
            raise NotConfigured('PROXY_LIST is empty')

        return cls(proxy_list)

    def process_request(self, request, spider):
        if request.meta.get('proxy') is None:
            return

        proxy = random.choice(self.proxy_list)
        request.meta['proxy'] = proxy
        spider.logger.debug(f'Using proxy: {proxy}')

class RegionMiddleware:
    def process_request(self, request, spider):
        # Устанавливаем Краснодар
        parsed_url = urlparse(request.url)
        if 'alkoteka.com' in parsed_url.netloc:
            request.cookies['region'] = 'krasnodar'
            request.headers['X-Region'] = 'krasnodar'