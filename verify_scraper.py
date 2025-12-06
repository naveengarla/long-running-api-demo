import requests
import time
import json
import sys

BASE_URL = "http://localhost:8001"

def run_verification():
    print(f"Submitting Web Scraper task to {BASE_URL}...")
    
    payload = {
        "task_type": "web_scrape",
        "url": "https://example.com",
        "metadata": {"source": "verification_script"},
        "duration": 5 # Ignored by scraper but required by schema validation if not fully optional in DB model? 
        # Schema has default, but let's send it to be safe.
    }
    
    try:
        response = requests.post(f"{BASE_URL}/tasks", json=payload)
        response.raise_for_status()
        data = response.json()
        task_id = data["task_id"]
        print(f"Task submitted: {task_id}")
    except Exception as e:
        print(f"Failed to submit task: {e}")
        sys.exit(1)

    print("Polling for completion...")
    while True:
        try:
            status_res = requests.get(f"{BASE_URL}/tasks/{task_id}")
            status_res.raise_for_status()
            status_data = status_res.json()
            status = status_data["status"]
            print(f"Status: {status}")
            
            if status == "SUCCESS":
                print("\nTask Completed Successfully!")
                print("Result Payload:")
                print(json.dumps(status_data.get("result_payload"), indent=2))
                break
            elif status in ["FAILED", "CANCELLED"]:
                print(f("\nTask Failed/Cancelled with status: {status}"))
                sys.exit(1)
            
            time.sleep(2)
        except Exception as e:
            print(f"Error polling status: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run_verification()
