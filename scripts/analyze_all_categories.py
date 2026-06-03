import requests
import re
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

CATEGORIES = [
    'https://ijiza.ru/catalog/hot/',
    'https://ijiza.ru/catalog/cold/',
    'https://ijiza.ru/catalog/universalnye-koptilni/',
    'https://ijiza.ru/catalog/horeca/',
    'https://ijiza.ru/catalog/profi/',
    'https://ijiza.ru/catalog/industrial/',
    'https://ijiza.ru/catalog/avtomaticheskie-koptilni/',
    'https://ijiza.ru/catalog/koptilnye-apparaty/',
    'https://ijiza.ru/catalog/koptilnye-shkafy/',
    'https://ijiza.ru/catalog/kamery-termodymovye/',
    'https://ijiza.ru/',
]

EXCLUDE = ['components', 'rashodnye-materialy', 'soputstvuyushie-tovary', 'vesy', 'vetchinnye-formy', 'other']

def get_links(url):
    r = requests.get(url, headers=headers, timeout=30, verify=False)
    text = r.content.decode('cp1251', errors='ignore')
    links = re.findall(r'href="(/catalog/detail/[^"]+)"', text)
    return sorted(set(links))

for url in CATEGORIES:
    links = get_links(url)
    products = [l for l in links if not any(e in l for e in EXCLUDE)]
    print(f'{url}: total={len(links)}, products={len(products)}')
    for p in products[:5]:
        print(f'  {p}')
    print()
