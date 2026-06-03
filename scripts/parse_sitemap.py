import requests
import re
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get('https://ijiza.ru/sitemap.xml', headers=headers, timeout=30, verify=False)
text = r.content.decode('utf-8', errors='ignore')

# Extract all URLs
urls = re.findall(r'<loc>([^<]+)</loc>', text)
print(f'Total URLs: {len(urls)}')

# Filter for product pages (cameras, not components)
product_urls = [u for u in urls if '/catalog/detail/' in u and 'components' not in u 
                and 'rashodnye-materialy' not in u and 'soputstvuyushie-tovary' not in u
                and 'vesy' not in u and 'vetchinnye-formy' not in u and 'other' not in u]

print(f'Product URLs: {len(product_urls)}')
for u in product_urls[:30]:
    print(u)

# Also find article URLs
article_urls = [u for u in urls if '/articles/' in u]
print(f'\nArticle URLs: {len(article_urls)}')
for u in article_urls[:20]:
    print(u)

# Save
import json
with open('docs/research/ijiza/sitemap_parsed.json', 'w', encoding='utf-8') as f:
    json.dump({'products': product_urls, 'articles': article_urls, 'all': urls}, f, ensure_ascii=False, indent=2)
