import time

import scrapy
import json
from urllib.parse import urlparse
import os
from random import choice
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message
import logging
from typing import Optional, List, Dict, Any

class AlkotekaProductSpider(scrapy.Spider):
    name = 'alkoteka'

    custom_settings = {
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429],
        'CONCURRENT_REQUESTS': 4,
        'DOWNLOAD_DELAY': 1,
        'LOG_LEVEL': 'INFO'
    }

    def __init__(self, start_url=None, region_uuid='4a70f9e0-46ae-11e7-83ff-00155d026416',
                 use_proxy=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url] if start_url else ['https://alkoteka.com/catalog/krepkiy-alkogol',
                                                         'https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',
                                                         'https://alkoteka.com/catalog/vino'
                                                        ]
        self.region_uuid = region_uuid
        self.use_proxy = use_proxy
        self.data_dir = 'product_data'
        self.proxy_pool = self._init_proxy_pool() if use_proxy else None

        self._configure_middlewares()

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            self.logger.info(f"Created directory {self.data_dir}")

    def _init_proxy_pool(self):
        return [
            'http://45.61.139.48:8000',
            'http://103.177.45.3:80',
            'http://20.210.113.32:80',
            'http://45.79.189.78:80'
        ]

    def _configure_middlewares(self):
        if self.use_proxy:
            if not hasattr(self, 'custom_settings'):
                self.custom_settings = {}
            self.custom_settings['DOWNLOADER_MIDDLEWARES'] = {
                'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
                'alkoteka_parser.middlewares.CustomRetryMiddleware': 550,
            }


    def start_requests(self):
        for url in self.start_urls:
            request = scrapy.Request(url, callback=self.parse_category)
            if self.use_proxy and self.proxy_pool:
                request.meta['proxy'] = choice(self.proxy_pool)
            yield request

    def parse_category(self, response):
        try:
            parsed_url = urlparse(response.url)
            path_parts = parsed_url.path.split('/')
            category_slug = path_parts[-1] if path_parts[-1] else path_parts[-2]

            api_url = (
                f"https://alkoteka.com/web-api/v1/product?"
                f"city_uuid={self.region_uuid}&"
                f"page=1&per_page=2000&root_category_slug={category_slug}"
            )

            request = scrapy.Request(
                api_url,
                callback=self.parse_product_list,
                meta={'category': category_slug}
            )

            if self.use_proxy and self.proxy_pool:
                request.meta['proxy'] = choice(self.proxy_pool)

            yield request

        except Exception as e:
            self.logger.error(f"Error in parse_category: {e}")

    def parse_product_list(self, response):
        try:
            data = json.loads(response.text)
            products = data.get('results', [])
            product_slugs = [p['slug'] for p in products if 'slug' in p]

            self.logger.info(f"Found {len(product_slugs)} products in {response.meta['category']}")

            for slug in product_slugs:
                product_url = (
                    f"https://alkoteka.com/web-api/v1/product/{slug}?"
                    f"city_uuid={self.region_uuid}"
                )

                request = scrapy.Request(
                    product_url,
                    callback=self.parse_product,
                    meta={
                        'slug': slug,
                        'category': response.meta['category']
                    },
                    errback=self.handle_error
                )

                if self.use_proxy and self.proxy_pool:
                    request.meta['proxy'] = choice(self.proxy_pool)

                yield request

        except Exception as e:
            self.logger.error(f"Error parsing product list: {e}")

    def parse_product(self, response):
        try:
            slug = response.meta['slug']
            category = response.meta['category']
            product_data = json.loads(response.text)

            product_data['region_uuid'] = self.region_uuid
            product_data['category'] = category

            self._save_product_data(product_data, category, slug)
            self._log_product_info(product_data)

        except Exception as e:
            self.logger.error(f"Error processing product: {e}")

    def transform_product_data(self, input_data: dict, category: str, slug: str) -> dict:
        # Основные данные из входного JSON
        results = input_data.get('results', {})
        if results is None:
            self.logger.error("Results is None")
            return {}

        # 1. Формирование названия товара
        name = results.get('name')
        if name is None:
            name = ''
        subname = results.get('subname')
        if subname is None:
            subname = ''
        base_title = name if name else subname

        # Сбор дополнительных атрибутов для названия
        color, volume = None, None
        filter_labels = results.get('filter_labels', [])
        if filter_labels is None:
            filter_labels = []

        for label in filter_labels:
            if label is None:
                continue
            filter_type = label.get('filter')
            if filter_type == 'cvet':
                color = label.get('title')
            elif filter_type == 'obem':
                volume = label.get('title')

        # Добавление цвета и объема к названию при необходимости
        title_parts = [base_title]
        if color is not None and color not in base_title:
            title_parts.append(color)
        if volume is not None and volume not in base_title:
            title_parts.append(volume)
        title = ", ".join(title_parts)

        # 2. Сбор маркетинговых тегов
        marketing_tags = []

        # Теги из специальных полей
        is_new = results.get('new')
        if is_new is not None and is_new:
            marketing_tags.append('Новинка')

        gift_package = results.get('gift_package')
        if gift_package is not None and gift_package:
            marketing_tags.append('Подарок')

        # Теги из price_details
        price_details = results.get('price_details', [])
        if price_details is None:
            price_details = []

        for detail in price_details:
            if detail is None:
                continue
            tag_title = detail.get('title')
            if tag_title is not None and tag_title not in marketing_tags:
                marketing_tags.append(tag_title)

        # Теги из filter_labels
        for label in filter_labels:
            if label is None:
                continue
            if label.get('filter') == 'tovary-so-skidkoi':
                tag_title = label.get('title')
                if tag_title is not None and tag_title not in marketing_tags:
                    marketing_tags.append(tag_title)

        # 3. Извлечение бренда
        brand = "Неизвестно"
        description_blocks = results.get('description_blocks', [])
        if description_blocks is None:
            description_blocks = []

        for block in description_blocks:
            if block is None:
                continue
            if block.get('code') == 'brend':
                values = block.get('values', [])
                if values is not None and len(values) > 0:
                    brand_name = values[0].get('name')
                    if brand_name is not None:
                        brand = brand_name
                        break

        # 4. Иерархия разделов
        section = []
        category_data = results.get('category', {})
        if category_data is None:
            category_data = {}

        parent_category = category_data.get('parent', {})
        if parent_category is None:
            parent_category = {}

        parent_name = parent_category.get('name')
        if parent_name is not None:
            section.append(parent_name)

        category_name = category_data.get('name')
        if category_name is not None:
            section.append(category_name)

        # 5. Данные о цене
        price = results.get('price')
        if price is None:
            current_price = 0.0
        else:
            try:
                current_price = float(price)
            except (TypeError, ValueError):
                current_price = 0.0

        prev_price = results.get('prev_price')
        if prev_price is None:
            original_price = current_price
        else:
            try:
                original_price = float(prev_price)
            except (TypeError, ValueError):
                original_price = current_price

        sale_tag = ""
        if original_price > current_price:
            discount_percent = round((1 - current_price / original_price) * 100)
            sale_tag = f"Скидка {discount_percent}%"

        # 6. Наличие товара
        available = results.get('available')
        if available is None:
            in_stock = False
        else:
            in_stock = bool(available)

        quantity_total = results.get('quantity_total')
        if quantity_total is None or not in_stock:
            stock_count = 0
        else:
            try:
                stock_count = int(quantity_total)
            except (TypeError, ValueError):
                stock_count = 0

        # 7. Медиа-контент
        main_image = results.get('image_url')
        if main_image is None:
            main_image = ''

        assets = {
            'main_image': main_image,
            'set_images': [main_image] if main_image else [],
            'view360': [],
            'video': []
        }

        # 8. Метаданные и описание
        metadata = {'__description': ''}

        # Добавление артикула
        vendor_code = results.get('vendor_code')
        if vendor_code is not None:
            metadata['Артикул'] = str(vendor_code)

        # Формирование описания из текстовых блоков
        description_parts = []
        text_blocks = results.get('text_blocks', [])
        if text_blocks is None:
            text_blocks = []

        for block in text_blocks:
            if block is None:
                continue
            content = block.get('content')
            if content is not None:
                description_parts.append(content)

        metadata['__description'] = " ".join(description_parts)

        # Добавление характеристик
        for block in description_blocks:
            if block is None:
                continue

            key = block.get('title')
            if key is None:
                continue

            # Обработка разных типов характеристик
            block_type = block.get('type')
            if block_type == 'select':
                values = []
                block_values = block.get('values', [])
                if block_values is not None:
                    for v in block_values:
                        if v is None:
                            continue
                        enabled = v.get('enabled')
                        if enabled is not None and enabled:
                            name = v.get('name')
                            if name is not None:
                                values.append(name)
                if values:
                    metadata[key] = ", ".join(values)

            elif block_type == 'range':
                unit = block.get('unit')
                if unit is None:
                    unit = ''

                min_val = block.get('min')
                max_val = block.get('max')

                if min_val is not None and max_val is not None:
                    if min_val == max_val:
                        metadata[key] = f"{min_val}{unit}"
                    else:
                        metadata[key] = f"{min_val}-{max_val}{unit}"

        # 9. Подсчет вариантов
        color_variants = 1
        volume_variants = 1

        for block in description_blocks:
            if block is None:
                continue

            code = block.get('code')
            if code == 'cvet' and block.get('type') == 'select':
                values = block.get('values', [])
                if values is not None:
                    color_variants = len([v for v in values if v is not None and v.get('enabled')])

            elif code == 'obem' and block.get('type') == 'select':
                values = block.get('values', [])
                if values is not None:
                    volume_variants = len([v for v in values if v is not None and v.get('enabled')])

        variants = color_variants * volume_variants

        # Формирование итоговых данных
        uuid = results.get('uuid')
        if uuid is None:
            uuid = ''

        return {
            'timestamp': int(time.time()),
            'RPC': uuid,
            'url': '',  # URL отсутствует в исходных данных
            'title': title,
            'marketing_tags': marketing_tags,
            'brand': brand,
            'section': section,
            'price_data': {
                'current': current_price,
                'original': original_price,
                'sale_tag': sale_tag
            },
            'stock': {
                'in_stock': in_stock,
                'count': stock_count
            },
            'assets': assets,
            'metadata': metadata,
            'variants': variants
        }

    def _save_product_data(self, product_data, category, slug):
        try:
            transformed_data = self.transform_product_data(product_data, category, slug)
            # Ensure data directory exists
            os.makedirs(self.data_dir, exist_ok=True)

            # Define single output file path
            output_file = os.path.join(self.data_dir, "all_products.jsonl")

            # Append to JSON Lines file
            with open(output_file, 'a', encoding='utf-8') as f:
                json_line = json.dumps(transformed_data, ensure_ascii=False)
                f.write(json_line + '\n')

            self.logger.info(f"Appended product (category: {category}, slug: {slug}) to {output_file}")
        except Exception as e:
            self.logger.error(f"Error saving product data (category: {category}, slug: {slug}): {e}")

    def _log_product_info(self, product_data):
        try:
            info = {
                'name': product_data.get('results', {}).get('name'),  # Достаем name из вложенного results
                'price': product_data.get('results', {}).get('price'),
                'prev_price': product_data.get('results', {}).get('prev_price'),
                'available': product_data.get('results', {}).get('quantity_total', 0) > 0,  # Проверяем наличие товара
                'region': self.region_uuid,
                'url': f"https://example.com/product/{product_data.get('results', {}).get('uuid')}"
            }
            self.logger.info(json.dumps(info, indent=2, ensure_ascii=False))
        except Exception as e:
            self.logger.error(f"Error logging product info: {e}")

    def handle_error(self, failure):
        try:
            self.logger.error(f"Request failed: {failure.value}")

            if not self.use_proxy or not hasattr(self, 'proxy_pool'):
                return

            request = failure.request
            if 'proxy' in request.meta and self.proxy_pool:
                bad_proxy = request.meta['proxy']
                self.logger.warning(f"Removing bad proxy: {bad_proxy}")
                if bad_proxy in self.proxy_pool:
                    self.proxy_pool.remove(bad_proxy)

                if self.proxy_pool:
                    new_proxy = choice(self.proxy_pool)
                    self.logger.info(f"Retrying with new proxy: {new_proxy}")
                    request.meta['proxy'] = new_proxy
                    yield request
                else:
                    self.logger.error("No proxies left in the pool")
        except Exception as e:
            self.logger.error(f"Error in handle_error: {e}")


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