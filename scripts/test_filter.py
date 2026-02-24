import os
import httpx

BACKEND_URL = os.getenv('BACKEND_URL', 'http://127.0.0.1:8000')
# filter for 2016-04-19
params = {
    'start_date': '2016-04-19T00:00:00',
    'end_date': '2016-04-19T23:59:59',
    'limit': 50
}
print('Requesting', BACKEND_URL + '/orders', 'with params', params)
try:
    r = httpx.get(BACKEND_URL + '/orders', params=params, timeout=10.0)
    print('status', r.status_code)
    try:
        j = r.json()
    except Exception:
        j = r.text
    print('response type:', type(j))
    if isinstance(j, list):
        print('count', len(j))
        for i, it in enumerate(j[:5]):
            print(i, it)
    else:
        print(j)
except Exception as e:
    print('error', e)
