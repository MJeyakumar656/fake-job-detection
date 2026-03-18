import requests

url = "https://www.naukri.com/jobapi/v3/job/160326502891"

headers_to_test = [
    {"appid": "109", "systemid": "Naukri"},
    {"appid": "109", "systemid": "109"},
    {"appid": "121", "systemid": "121"},
    {"appid": "105", "systemid": "105"}
]

for h in headers_to_test:
    print(f"\nTesting headers: {h}")
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        'Accept': 'application/json',
    }
    headers.update(h)
    
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print("SUCCESS! Data keys:", list(resp.json().keys()))
        else:
            print("Response:", resp.text[:100])
    except Exception as e:
        print("Error:", e)
