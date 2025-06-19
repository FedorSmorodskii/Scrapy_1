# Парсер товаров Alkoteka

Scrapy-паук для сбора данных о продуктах с сайта alkoteka.com.

## Возможности

- Сбор данных из нескольких категорий товаров
- Поддержка региональных цен через UUID
- Работа через прокси с автоматической ротацией
- Структурированный вывод в JSON
- Обработка ошибок и повторные запросы

## Установка

```bash
pip install scrapy
```

# Использование
## Базовый запуск (без прокси)
```bash
scrapy runspider alkoteka_spider.py
```

## С поддержкой прокси
```bash
scrapy runspider alkoteka_spider.py -a use_proxy=True
```

## С указанием региона
```bash
scrapy runspider alkoteka_spider.py -a region_uuid=ваш_uuid_региона
```

## Со всеми параметрами
```bash
scrapy runspider alkoteka_spider.py -a start_url="https://alkoteka.com/category" region_uuid="ваш_uuid" use_proxy=True
```


### В случае технических шоколадок
```bash
scrapy crawl alkoteka
```
