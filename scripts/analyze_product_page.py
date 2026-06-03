import requests
import re
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

url = 'https://ijiza.ru/catalog/info/smoking/termokamera-dlya-goryachego-kopcheniya-izhitca-z115/'
r = requests.get(url, headers=headers, timeout=30, verify=False)
text = r.content.decode('cp1251', errors='ignore')

# Save full HTML for inspection
with open('scripts/ijiza_product_sample.html', 'w', encoding='utf-8') as f:
    f.write(text)

# Look for price patterns
print('=== PRICE PATTERNS ===')
price_patterns = [
    r'(\d[\d\s]*\d)\s*руб',
    r'(\d[\d\s]*\d)\s*₽',
    r'price[^>]*>([^<]+)',
    r'цена[^>]*>([^<]+)',
    r'стоимость[^>]*>([^<]+)',
]
for pattern in price_patterns:
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        print(f'Pattern "{pattern[:40]}" -> {matches[:3]}')

# Look for spec table
print('\n=== SPEC PATTERNS ===')
# Try to find table rows with specs
table_rows = re.findall(r'<tr[^>]*>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?</tr>', text, re.DOTALL | re.IGNORECASE)
for row in table_rows[:15]:
    key = re.sub(r'<[^>]+>', '', row[0]).strip()
    val = re.sub(r'<[^>]+>', '', row[1]).strip()
    if key and val and len(key) < 50:
        print(f'{key}: {val}')

# Look for any structured data (JSON-LD)
print('\n=== JSON-LD ===')
jsonld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', text, re.DOTALL)
for j in jsonld[:2]:
    print(j[:500])
