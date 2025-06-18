import scrapy
import time
from urllib.parse import urljoin
from ..items import AlkotekaParserItem


class AlkotekaSpider(scrapy.Spider):
    name = 'alkoteka'
    allowed_domains = ['alkoteka.com']

    start_urls = [
        'https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',
        'https://alkoteka.com/catalog/vino',
        'https://alkoteka.com/catalog/pivo'
    ]

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'CONCURRENT_REQUESTS': 1,
        'FEED_FORMAT': 'json',
        'FEED_URI': 'result.json'
    }

    def parse(self, response):
        product_links = response.css('a.product-card__link::attr(href)').getall()

        if not product_links:
            self.logger.warning(f'Не найдено товаров на странице: {response.url}')
            return

        for link in product_links:
            yield response.follow(
                url=urljoin(response.url, link),
                callback=self.parse_product,
                meta={'category_url': response.url}
            )

        next_page = response.css('a.pagination__next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_product(self, response):
        item = AlkotekaParserItem()

        item['timestamp'] = int(time.time())
        item['url'] = response.url
        item['RPC'] = response.url.split('/')[-1]

        title = response.css('h1.product__title::text').get('').strip()
        volume = response.css('span.product__volume::text').get()
        if volume:
            title = f"{title}, {volume.strip()}"
        item['title'] = title

        # Цены
        current_price = response.css('span.product__price::attr(data-value)').get()
        original_price = response.css('span.product__old-price::attr(data-value)').get(current_price)

        item['price_data'] = {
            'current': float(current_price.replace(' ', '')) if current_price else 0.0,
            'original': float(original_price.replace(' ', '')) if original_price else 0.0,
            'sale_tag': f"Скидка {int((1 - float(current_price) / float(original_price)) * 100)}%"
            if original_price and float(original_price) > float(current_price) else ""
        }

        # Наличие
        in_stock = bool(response.css('div.product__available').get())
        item['stock'] = {
            'in_stock': in_stock,
            'count': 10 if in_stock else 0  # Примерное значение
        }

        # Изображения
        main_image = response.css('div.product-slider__main img::attr(src)').get()
        set_images = response.css('div.product-slider__thumbs img::attr(src)').getall()

        item['assets'] = {
            'main_image': urljoin(response.url, main_image) if main_image else '',
            'set_images': [urljoin(response.url, img) for img in set_images] if set_images else [],
            'view360': [],
            'video': []
        }

        # Метаданные
        item['metadata'] = {
            '__description': ' '.join(response.css('div.product__description *::text').getall()).strip(),
            'attributes': {
                spec.css('div.product-specs__name::text').get('').strip():
                    spec.css('div.product-specs__value::text').get('').strip()
                for spec in response.css('div.product-specs__row')
            }
        }

        # Категории (из хлебных крошек)
        item['section'] = response.css('nav.breadcrumbs a::text').getall()[1:]

        yield item