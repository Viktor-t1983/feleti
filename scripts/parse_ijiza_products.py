import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests
import re
import json
import time
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.9',
}

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30, verify=False)
        return r.content.decode('cp1251', errors='ignore')
    except Exception as e:
        print(f'ERROR fetching {url}: {e}')
        return None

def parse_product_page(url):
    text = fetch(url)
    if not text:
        return None
    
    # Title
    title_match = re.search(r'<title>(.*?)</title>', text, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else None
    
    # Clean title (remove site name)
    if title and '|' in title:
        title = title.split('|')[0].strip()
    
    # Price
    price_match = re.search(r'([\d\s]+)\s*₽', text)
    price = None
    if price_match:
        price_str = price_match.group(1).replace(' ', '').replace('\xa0', '')
        try:
            price = int(price_str)
        except:
            pass
    
    # Description - try meta description
    desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', text, re.IGNORECASE)
    description = desc_match.group(1) if desc_match else None
    
    # Try to find specs table
    specs = {}
    # Look for patterns like "Загрузка: 100 кг" or table rows
    spec_patterns = [
        (r'Загрузка[:\s]+([\d\s]+)\s*кг', 'max_load_kg'),
        (r'Габариты[^\d]*([\d\s]+\s*x\s*[\d\s]+\s*x\s*[\d\s]+)', 'dimensions_mm'),
        (r'Мощность[:\s]+([\d\s,]+)\s*кВт', 'power_kw'),
        (r'Напряжение[:\s]+(\d+)\s*В', 'voltage_v'),
        (r'Объ[её]м[:\s]+([\d\s,]+)\s*м³', 'volume_m3'),
    ]
    for pattern, key in spec_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            specs[key] = m.group(1).strip()
    
    return {
        'url': url,
        'title': title,
        'price_rub': price,
        'description': description,
        'specs': specs,
    }

def get_camera_urls():
    r = requests.get('https://ijiza.ru/sitemap.xml', headers=HEADERS, timeout=30, verify=False)
    text = r.content.decode('utf-8', errors='ignore')
    urls = re.findall(r'<loc>([^<]+)</loc>', text)
    
    keywords = ['izhitca', 'varmen', 'z115', 'z250', 'gk', 'm4', '1200', '2500', 'mini', 'uni', 'utr']
    camera_urls = []
    for u in urls:
        if '/catalog/info/' in u and any(k in u.lower() for k in keywords):
            if 'components' not in u and 'rashodnye' not in u and 'soputstvuyushie' not in u:
                camera_urls.append(u)
    return sorted(set(camera_urls))

def main():
    urls = get_camera_urls()
    print(f'Found {len(urls)} camera URLs')
    
    products = []
    for i, url in enumerate(urls):
        print(f'[{i+1}/{len(urls)}] Parsing {url}...')
        product = parse_product_page(url)
        if product:
            products.append(product)
            print(f'  -> {product["title"]} | {product["price_rub"]} rub')
        time.sleep(0.5)  # Be polite
    
    # Save
    output = {
        'source': 'ijiza.ru',
        'date': '2026-06-03',
        'total': len(products),
        'products': products,
    }
    
    with open('docs/research/ijiza/catalog_parsed.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'\nSaved {len(products)} products to docs/research/ijiza/catalog_parsed.json')

if __name__ == '__main__':
    main()
