import requests
try:
    r = requests.get("http://localhost:8001/", timeout=2)
    print(f"Root status: {r.status_code}")
except Exception as e:
    print(f"Root failed: {e}")

try:
    r = requests.get("http://localhost:8001/docs", timeout=2)
    print(f"Docs status: {r.status_code}")
except Exception as e:
    print(f"Docs failed: {e}")
