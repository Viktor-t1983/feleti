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

# Parse main page for article links
main = fetch('https://ijiza.ru/')
article_links = sorted(set(re.findall(r'href="(/articles/[^"]+)"', main)))
print(f'Articles: {len(article_links)}')
for a in article_links[:10]:
    print(f'  {a}')

# Parse catalog categories
catalog = fetch('https://ijiza.ru/catalog')
cat_links = sorted(set(re.findall(r'href="(/catalog/[a-z-]+/)"', catalog)))
print(f'\nCatalog categories: {len(cat_links)}')
for c in cat_links:
    print(f'  {c}')

# Parse product pages from catalog
product_links = sorted(set(re.findall(r'href="(/catalog/detail/[^"]+)"', catalog)))
print(f'\nProducts/components: {len(product_links)}')
for p in product_links[:10]:
    print(f'  {p}')
