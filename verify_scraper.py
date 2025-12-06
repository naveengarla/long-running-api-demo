import requests
import time
import json
import sys

BASE_URL = "http://localhost:8001"

def run_verification():
    print(f"Submitting Web Scraper task to {BASE_URL} for Wikipedia...")
    
    payload = {
        "task_type": "web_scrape",
        "url": "https://en.wikipedia.org/wiki/India",
        "metadata": {"source": "verification_script"},
        "duration": 5 
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
                # Ideally we want to see the error log or message here
                print("Logs:")
                for log in status_data.get("logs", []):
                    print(f"[{log['level']}] {log['message']}")
                
                # If it failed, that's okay IF it is a legitimate failure, but for Wikipedia we expect SUCCESS now.
                sys.exit(1)
            
            time.sleep(2)
        except Exception as e:
            print(f"Error polling status: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run_verification()
