import os
import time
import datetime
from celery import Task
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import pybreaker
from app.core.database import SessionLocal
from app.models.job import Job, JobLog, JobStatus
from app.services.mock_external import MockExternalService
from app.core.celery_app import celery_app

# --- Resiliency Configuration ---

# Circuit Breaker: Trip after 5 consecutive failures, reset timeout 60s
# Excludes ConnectionError from tripping? No, usually ConnectionError IS what trips it.
# We will wrap the service call with this breaker.
service_breaker = pybreaker.CircuitBreaker(state_storage=pybreaker.CircuitMemoryStorage(pybreaker.STATE_CLOSED), fail_max=5, reset_timeout=60)

mock_service = MockExternalService(failure_rate=0.3) # 30% failure chance

@service_breaker
@retry(
    stop=stop_after_attempt(5), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(ConnectionError),
    reraise=True
)
def call_external_service_safely(data: list, metadata: dict):
    """
    Calls the external service with Retry (Tenacity) and Circuit Breaker (PyBreaker) protection.
    """
    return mock_service.perform_risky_operation(data, metadata)

class DatabaseTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        job_id = kwargs.get('job_id') or (args[0] if args else None)
        if job_id:
            with SessionLocal() as db:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.status = JobStatus.SUCCESS.value
                    job.result_payload = retval
                    job.completed_at = datetime.datetime.utcnow()
                    db.commit()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job_id = kwargs.get('job_id') or (args[0] if args else None)
        if job_id:
            with SessionLocal() as db:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.status = JobStatus.FAILED.value
                    # Log the error
                    log = JobLog(job_id=job_id, level="ERROR", message=str(exc))
                    db.add(log)
                    job.completed_at = datetime.datetime.utcnow()
                    db.commit()

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        job_id = kwargs.get('job_id') or (args[0] if args else None)
        if job_id:
            with SessionLocal() as db:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    job.retry_count += 1
                    log = JobLog(job_id=job_id, level="WARNING", message=f"Retrying task: {str(exc)}")
                    db.add(log)
                    db.commit()

def log_to_db(job_id: str, message: str, level: str = "INFO"):
    with SessionLocal() as db:
        log = JobLog(job_id=job_id, level=level, message=message)
        db.add(log)
        db.commit()

@celery_app.task(name="process_vector_data", base=DatabaseTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def process_vector_data(self, job_id: str, vector_data: list[float], metadata: dict, duration: int = 10):
    """
    Simulates a long-running vector DB operation with progress updates and persistence.
    """
    # Update status to RUNNING
    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.RUNNING.value
            job.started_at = datetime.datetime.utcnow()
            db.commit()

    log_to_db(job_id, "Task started processing.")

    total_steps = duration
    for i in range(total_steps):
        # Check if cancelled (optional optimization, Celery revoke handles the kill)
        # But updating DB status if revoked is handled by Celery state, 
        # though we might want to check DB status here if we implement soft cancellation.
        
        time.sleep(1)
        
        message = f'Processing chunk {i + 1}/{total_steps}...'
        self.update_state(state='PROGRESS', meta={
            'current': i + 1,
            'total': total_steps,
            'message': message,
            'job_id': job_id
        })
        
        # Log progress every 20% or so to avoid spamming DB
        
        # Log progress every 20% or so to avoid spamming DB
        if i % max(1, total_steps // 5) == 0:
            log_to_db(job_id, message)
            
            # --- Demonstrate Resiliency ---
            # Every checkpoint, try to call the external service
            try:
                result = call_external_service_safely(vector_data, metadata)
                log_to_db(job_id, f"External Service Success: {result['external_id']}")
            except pybreaker.CircuitBreakerError:
                log_to_db(job_id, "External Service Skipped (Circuit Breaker OPEN)", level="WARNING")
            except Exception as e:
                log_to_db(job_id, f"External Service Failed after retries: {str(e)}", level="ERROR")
                # We might choose to NOT fail the whole task, or we might.
                # For demo, let's keep going but log error.
    
    log_to_db(job_id, "Task processing complete.")

    # Simulate a result
    return {
        "processed_vectors": len(vector_data),
        "status": "indexed",
        "metadata_processed": metadata
    }
