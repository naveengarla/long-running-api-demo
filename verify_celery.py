from app.worker import process_vector_data
import time

def test_direct_celery():
    print("Pushing task directly to Celery...")
    result = process_vector_data.delay(
        job_id="test_direct_123", 
        vector_data=[1,2,3], 
        metadata={}, 
        duration=5
    )
    print(f"Task pushed: {result.id}")
    
    # Wait and check status
    for i in range(10):
        print(f"Status: {result.status}")
        if result.status == 'SUCCESS':
            print("SUCCESS!")
            break
        time.sleep(1)

if __name__ == "__main__":
    test_direct_celery()
