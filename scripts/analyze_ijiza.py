import requests
import re
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

r = requests.get('https://ijiza.ru/catalog/termokamera-dlya-kopcheniya/', headers=headers, timeout=30, verify=False)
text = r.content.decode('cp1251', errors='ignore')

# Save a snippet
with open('scripts/ijiza_sample.html', 'w', encoding='utf-8') as f:
    f.write(text[:10000])

# Look for product patterns
print('href=/catalog/detail/ count:', len(re.findall(r'href="/catalog/detail/', text)))
print('href=/catalog/ count:', len(re.findall(r'href="/catalog/', text)))
print('product count:', len(re.findall(r'product', text)))
print('item count:', len(re.findall(r'item', text)))
print('card count:', len(re.findall(r'card', text)))
