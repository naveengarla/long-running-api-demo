import requests
import time
import sys

BASE_URL = "http://localhost:8001"

def submit_task():
    print("Submitting task...")
    payload = {
        "vector_data": [0.1, 0.2, 0.3],
        "metadata": {"test": "persistence"},
        "duration": 5
    }
    response = requests.post(f"{BASE_URL}/tasks", json=payload)
    if response.status_code != 202:
        print(f"Failed to submit task: {response.text}")
        sys.exit(1)
    task_id = response.json()["task_id"]
    print(f"Task submitted: {task_id}")
    return task_id

def get_task_status(task_id):
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    if response.status_code != 200:
        print(f"Failed to get status: {response.text}")
        return None
    return response.json()

def get_task_logs(task_id):
    response = requests.get(f"{BASE_URL}/tasks/{task_id}/logs")
    if response.status_code != 200:
        print(f"Failed to get logs: {response.text}")
        return []
    return response.json()

def cancel_task(task_id):
    print(f"Cancelling task {task_id}...")
    response = requests.delete(f"{BASE_URL}/tasks/{task_id}")
    if response.status_code != 204:
        print(f"Failed to cancel task: {response.text}")
    else:
        print("Task cancelled successfully.")

def verify_persistence():
    # 1. Submit a task
    task_id = submit_task()
    
    # 2. Poll for completion
    print("Polling for completion...")
    for _ in range(10):
        status = get_task_status(task_id)
        print(f"Status: {status['status']}")
        if status['status'] in ['SUCCESS', 'FAILED']:
            break
        time.sleep(1)
    
    # 3. Check logs
    logs = get_task_logs(task_id)
    print(f"Logs found: {len(logs)}")
    for log in logs:
        print(f"[{log['timestamp']}] {log['level']}: {log['message']}")
    
    if len(logs) == 0:
        print("ERROR: No logs found!")
    
    # 4. List tasks
    print("Listing tasks...")
    response = requests.get(f"{BASE_URL}/tasks")
    tasks = response.json()
    print(f"Total tasks in DB: {len(tasks)}")
    
    # 5. Verify Cancellation
    print("\nVerifying Cancellation...")
    task_id_2 = submit_task()
    time.sleep(1) # Let it start
    cancel_task(task_id_2)
    
    time.sleep(1)
    status_2 = get_task_status(task_id_2)
    print(f"Cancelled Task Status: {status_2['status']}")
    if status_2['status'] == 'CANCELLED':
        print("Cancellation verified.")
    else:
        print(f"ERROR: Task status is {status_2['status']}, expected CANCELLED")

if __name__ == "__main__":
    try:
        verify_persistence()
    except requests.exceptions.ConnectionError:
        print("Could not connect to API. Is it running?")
