import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def verify():
    print("1. Submitting task...")
    payload = {
        "vector_data": [0.1, 0.2, 0.3, 0.4, 0.5],
        "metadata": {"source": "user_upload", "type": "text_embedding"}
    }
    try:
        response = requests.post(f"{BASE_URL}/tasks", json=payload)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Is it running?")
        sys.exit(1)

    task_data = response.json()
    task_id = task_data["task_id"]
    print(f"Task submitted! ID: {task_id}")

    print("2. Polling for status...")
    while True:
        status_response = requests.get(f"{BASE_URL}/tasks/{task_id}")
        status_data = status_response.json()
        status = status_data["status"]
        
        print(f"Current status: {status}")
        
        if status == "SUCCESS":
            print("Task completed successfully!")
            print(f"Result: {status_data['result']}")
            break
        elif status == "FAILURE":
            print("Task failed!")
            sys.exit(1)
        
        time.sleep(1)

if __name__ == "__main__":
    verify()
