import requests
import re
import json
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9',
}

def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30, verify=False)
    return r.content.decode('cp1251', errors='ignore')

def extract_products_from_category(url):
    text = fetch(url)
    # Find product cards
    products = []
    # Try to find product links in category page
    links = re.findall(r'href="(/catalog/detail/[a-z0-9-]+/)"', text)
    for link in sorted(set(links)):
        if 'components' not in link:
            products.append(link)
    return products

# Categories to parse
CATEGORIES = [
    'https://ijiza.ru/catalog/avtomaticheskie-koptilni/',
    'https://ijiza.ru/catalog/hot/',
    'https://ijiza.ru/catalog/cold/',
    'https://ijiza.ru/catalog/universalnye-koptilni/',
    'https://ijiza.ru/catalog/horeca/',
    'https://ijiza.ru/catalog/profi/',
    'https://ijiza.ru/catalog/industrial/',
    'https://ijiza.ru/catalog/termokamera-dlya-kopcheniya/',
    'https://ijiza.ru/catalog/koptilnye-apparaty/',
    'https://ijiza.ru/catalog/koptilnye-shkafy/',
    'https://ijiza.ru/catalog/kamery-termodymovye/',
]

all_products = {}
for cat_url in CATEGORIES:
    print(f'Parsing {cat_url}...')
    products = extract_products_from_category(cat_url)
    cat_name = cat_url.rstrip('/').split('/')[-1]
    all_products[cat_name] = products
    print(f'  Found {len(products)} products')

# Save
with open('docs/research/ijiza/catalog_products.json', 'w', encoding='utf-8') as f:
    json.dump(all_products, f, ensure_ascii=False, indent=2)

print(f'\nTotal categories parsed: {len(CATEGORIES)}')
print(f'Total unique products: {sum(len(v) for v in all_products.values())}')
