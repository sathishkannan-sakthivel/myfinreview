import httpx

symbols=['^NSENI','^NSEI','^NFX50','^NSE50','^NSENEXT50','^NSENI50','^NN50','^NIFTYNEXT50','^NIFTYNS50','^NSEI50','^NIFTY','^NSE']
for s in symbols:
    try:
        r=httpx.get(f'https://query1.finance.yahoo.com/v8/finance/chart/{s}', timeout=5)
        print(s, r.status_code)
    except Exception as e:
        print(s, 'error', e)
