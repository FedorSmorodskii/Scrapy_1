from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
from random import choice

class CustomRetryMiddleware(RetryMiddleware):
    def process_response(self, request, response, spider):
        if response.status in [403, 429] and getattr(spider, 'use_proxy', False):
            reason = response_status_message(response.status)
            if hasattr(spider, 'proxy_pool') and spider.proxy_pool:
                new_proxy = choice(spider.proxy_pool)
                spider.logger.warning(f'Switching proxy to {new_proxy} after {response.status} response')
                request.meta['proxy'] = new_proxy
                return self._retry(request, reason, spider) or response
        return response