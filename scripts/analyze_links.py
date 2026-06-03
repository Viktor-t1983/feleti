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

# Find all /catalog/detail/ links
all_links = re.findall(r'href="(/catalog/detail/[^"]+)"', text)
unique = sorted(set(all_links))

print(f'Total unique detail links: {len(unique)}')
print('\n--- Non-component links (cameras/products): ---')
for link in unique:
    if 'components' not in link:
        print(link)

print('\n--- Component links: ---')
for link in unique:
    if 'components' in link:
        print(link)
