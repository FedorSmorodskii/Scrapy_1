
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

## Использование

### Базовый запуск (без прокси)
```bash
cd alkoteka_parser/alkoteka_parser/spiders
scrapy crawl alkoteka
```

### С поддержкой прокси
```bash
cd alkoteka_parser/alkoteka_parser/spiders
scrapy crawl alkoteka -a use_proxy=True
```

### С указанием региона
```bash
cd alkoteka_parser/alkoteka_parser/spiders
scrapy crawl alkoteka -a region_uuid=ваш_uuid_региона
```

### Со всеми параметрами
```bash
cd alkoteka_parser/alkoteka_parser/spiders
scrapy crawl alkoteka -a start_url="https://alkoteka.com/category" region_uuid="ваш_uuid" use_proxy=True
```

### В случае технических шоколадок
```bash
scrapy crawl alkoteka
```
