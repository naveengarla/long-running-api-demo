import os
import time
from celery import Celery

# Get Redis URL from environment variables
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery = Celery(__name__)
celery.conf.broker_url = CELERY_BROKER_URL
celery.conf.result_backend = CELERY_RESULT_BACKEND

@celery.task(name="process_vector_data", bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def process_vector_data(self, vector_data: list[float], metadata: dict, duration: int = 10):
    """
    Simulates a long-running vector DB operation with progress updates.
    """
    total_steps = duration
    for i in range(total_steps):
        time.sleep(1)
        self.update_state(state='PROGRESS', meta={
            'current': i + 1,
            'total': total_steps,
            'message': f'Processing chunk {i + 1}/{total_steps}...'
        })
    
    # Simulate a result
    return {
        "processed_vectors": len(vector_data),
        "status": "indexed",
        "metadata_processed": metadata
    }
