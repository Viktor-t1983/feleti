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
        # Try UTF-8 first, then fallback to cp1251
        for enc in ['utf-8', 'cp1251']:
            try:
                return r.content.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return r.content.decode('utf-8', errors='ignore')
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
    if title and '|' in title:
        title = title.split('|')[0].strip()
    
    # Price - look for pattern like "890 000 р."
    price = None
    price_match = re.search(r'([\d\s]+)\s*р\.?', text)
    if price_match:
        price_str = price_match.group(1).replace(' ', '').replace('\xa0', '')
        try:
            price = int(price_str)
        except:
            pass
    
    # Description from meta
    desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', text, re.IGNORECASE)
    description = desc_match.group(1) if desc_match else None
    
    # Specs from table rows
    specs = {}
    table_rows = re.findall(r'<tr[^>]*>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?</tr>', text, re.DOTALL | re.IGNORECASE)
    for row in table_rows:
        key = re.sub(r'<[^>]+>', '', row[0]).strip()
        val = re.sub(r'<[^>]+>', '', row[1]).strip()
        if key and val and len(key) < 60:
            # Normalize key
            key_norm = key.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('.', '')
            specs[key_norm] = val
    
    # Also extract from JSON-LD Product if available
    jsonld_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.DOTALL)
    if jsonld_match:
        try:
            ld = json.loads(jsonld_match.group(1))
            if isinstance(ld, dict) and ld.get('@type') == 'Product':
                if not description and ld.get('description'):
                    description = ld['description']
                if ld.get('offers') and isinstance(ld['offers'], dict):
                    offer_price = ld['offers'].get('price')
                    if offer_price and not price:
                        try:
                            price = int(offer_price)
                        except:
                            pass
        except:
            pass
    
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
            price_str = f'{product["price_rub"]} rub' if product['price_rub'] else 'no price'
            print(f'  -> {product["title"][:70]} | {price_str} | specs={len(product["specs"])}')
        time.sleep(0.5)
    
    output = {
        'source': 'ijiza.ru',
        'date': '2026-06-03',
        'total': len(products),
        'products': products,
    }
    
    with open('docs/research/ijiza/catalog_parsed.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f'\nSaved {len(products)} products')
    with_price = sum(1 for p in products if p['price_rub'])
    with_specs = sum(1 for p in products if p['specs'])
    print(f'With price: {with_price}, With specs: {with_specs}')

if __name__ == '__main__':
    main()
