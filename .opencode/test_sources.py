import httpx

r = httpx.post('http://localhost:8000/api/v1/auth/login/json', json={'username':'admin','password':'admin'})
token = r.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

r = httpx.get('http://localhost:8000/api/v1/sources/', headers=headers)
print('GET /sources/:', r.status_code)
if r.status_code == 200:
    data = r.json()
    for s in data:
        print(f'  {s["domain"]:25s} score={s["score"]} bl={s["is_blacklisted"]}')
else:
    print(r.text[:500])

r = httpx.post('http://localhost:8000/api/v1/sources/', headers=headers, json={'domain':'test.ru','score':2,'label':'Test'})
print('POST:', r.status_code, r.text[:200])

# Verify and cleanup
r = httpx.get('http://localhost:8000/api/v1/sources/', headers=headers)
data = r.json()
for s in data:
    if s['domain'] == 'test.ru':
        sid = s['id']
        r = httpx.put(f'http://localhost:8000/api/v1/sources/{sid}', headers=headers, json={'score':1,'is_blacklisted':True})
        print('PUT:', r.status_code, r.text[:200])
        r = httpx.delete(f'http://localhost:8000/api/v1/sources/{sid}', headers=headers)
        print('DELETE:', r.status_code)
        break

# Verify source not found 404
r = httpx.get(f'http://localhost:8000/api/v1/sources/99999', headers=headers)
print('GET 404:', r.status_code)
