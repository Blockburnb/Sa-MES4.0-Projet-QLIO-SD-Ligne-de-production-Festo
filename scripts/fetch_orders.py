import os
import httpx

BACKEND_URL = os.getenv('BACKEND_URL','http://127.0.0.1:8000')
print('Using', BACKEND_URL)
try:
    r = httpx.get(BACKEND_URL + '/orders')
    print('status', r.status_code)
    print(r.json())
except Exception as e:
    print('error', e)
