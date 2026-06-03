import requests
import re
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get('https://ijiza.ru/sitemap.xml', headers=headers, timeout=30, verify=False)
text = r.content.decode('utf-8', errors='ignore')

urls = re.findall(r'<loc>([^<]+)</loc>', text)

# Look for camera-related URLs
keywords = ['izhitca', 'varmen', 'z115', 'z250', 'gk', 'm4', '1200', '2500', 'mini', 'uni', 'utr']
camera_urls = []
for u in urls:
    if any(k in u.lower() for k in keywords) and 'components' not in u and 'rashodnye' not in u:
        camera_urls.append(u)

print(f'Camera-related URLs: {len(camera_urls)}')
for u in sorted(set(camera_urls))[:30]:
    print(u)

# Also look for any catalog URLs that are not components/materials/services
catalog_urls = [u for u in urls if '/catalog/' in u and 'components' not in u 
                and 'rashodnye' not in u and 'soputstvuyushie' not in u 
                and 'vesy' not in u and 'vetchinnye' not in u and 'other' not in u
                and 'uslugi' not in u]

print(f'\nAll catalog URLs: {len(catalog_urls)}')
for u in sorted(set(catalog_urls))[:30]:
    print(u)
