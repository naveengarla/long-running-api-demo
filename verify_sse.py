import requests
import json
import sys

def test_sse():
    # 1. Create Task
    url = "http://127.0.0.1:8001/tasks"
    payload = {
        "vector_data": [0.1, 0.2, 0.3],
        "metadata": {"user": "sse_test"},
        "duration": 5
    }
    
    print(f"Creating task...")
    try:
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code != 202:
            print(f"Failed to create task: {resp.text}")
            return
        
        task_id = resp.json().get("task_id")
        print(f"Task created: {task_id}")
        
        # 2. Stream
        stream_url = f"http://127.0.0.1:8001/tasks/{task_id}/stream"
        print(f"Listening to stream: {stream_url}")
        
        with requests.get(stream_url, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith("data: "):
                        data_str = decoded.replace("data: ", "")
                        data = json.loads(data_str)
                        status = data.get("status")
                        print(f"Update: {status} | Result: {data.get('result')}")
                        
                        if status in ["SUCCESS", "FAILURE", "REVOKED"]:
                            print("Task finished.")
                            break
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sse()
