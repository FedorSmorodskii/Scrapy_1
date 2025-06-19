import json
import os


class AlkotekaParserPipeline:
    def __init__(self):
        self.data_dir = 'product_data'
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def process_item(self, item, spider):
        category = item.get('category')
        slug = item.get('slug')

        if category and slug:
            category_dir = os.path.join(self.data_dir, category)
            os.makedirs(category_dir, exist_ok=True)

            filename = os.path.join(category_dir, f"{slug}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dict(item), f, ensure_ascii=False, indent=2)

        return item