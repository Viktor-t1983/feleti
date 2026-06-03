import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
}

urls = [
    'https://ijiza.ru',
    'https://ijiza.ru/catalog',
    'https://ijiza.ru/products',
]

for url in urls:
    try:
        r = requests.get(url, headers=headers, timeout=15, verify=False)
        print(f'{url}: status={r.status_code}, len={len(r.text)}')
        if r.status_code == 200:
            start = r.text.find('<title')
            if start != -1:
                start = r.text.find('>', start) + 1
                end = r.text.find('</title>', start)
                print(f'  title: {r.text[start:end]}')
    except Exception as e:
        print(f'{url}: ERROR {e}')
