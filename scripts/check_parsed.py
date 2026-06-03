import json

with open('docs/research/ijiza/catalog_parsed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('Total products:', data['total'])
print('Products with price:', sum(1 for p in data['products'] if p['price_rub']))
print('Products without price:', sum(1 for p in data['products'] if not p['price_rub']))
print()
for p in data['products'][:10]:
    price = p['price_rub']
    specs = p['specs']
    title = p['title'][:60] if p['title'] else 'No title'
    print(f"- {title}... | price={price} | specs={specs}")
