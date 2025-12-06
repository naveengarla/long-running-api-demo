import requests

try:
    print("Checking Root...")
    r = requests.get("http://localhost:8000/", timeout=5)
    print(r.status_code)
    print(r.text)

    print("Checking Docs...")
    r = requests.get("http://localhost:8000/docs", timeout=5)
    print(r.status_code)
except Exception as e:
    print(e)
