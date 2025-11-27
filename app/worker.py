import os
import time
from celery import Celery

# Get Redis URL from environment variables
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery = Celery(__name__)
celery.conf.broker_url = CELERY_BROKER_URL
celery.conf.result_backend = CELERY_RESULT_BACKEND

@celery.task(name="process_vector_data", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def process_vector_data(vector_data: list[float], metadata: dict):
    """
    Simulates a long-running vector DB operation.
    """
    # Simulate processing time (e.g., 10 seconds)
    time.sleep(10)
    
    # Simulate a result
    return {
        "processed_vectors": len(vector_data),
        "status": "indexed",
        "metadata_processed": metadata
    }
