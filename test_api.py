import requests
import json
import time

def test_api():
    url = "http://localhost:8000/tasks"
    payload = {
        "vector_data": [0.1, 0.2, 0.3],
        "metadata": {"user": "test"},
        "duration": 5
    }
    
    print(f"Sending POST to {url}...")
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 202:
            task_id = response.json().get("task_id")
            print(f"Task created: {task_id}")
            
            # Poll status
            for _ in range(5):
                time.sleep(1)
                status_url = f"http://localhost:8000/tasks/{task_id}"
                resp2 = requests.get(status_url)
                print(f"Status Check: {resp2.json()}")
        else:
            print("Failed to create task.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
