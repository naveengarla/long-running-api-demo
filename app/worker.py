"""
Celery Worker Module.
Contains the actual business logic for long-running tasks.
Implements:
1. Database Persistence (via DatabaseTask base class)
2. Resiliency Patterns (Circuit Breaker, Retries)
3. Observability (OpenTelemetry instrumentation)
"""
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
import requests
from bs4 import BeautifulSoup

from app.core.celery_app import celery_app

# --- Resiliency Configuration ---

# Circuit Breaker: Trip after 5 consecutive failures, reset timeout 60s
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
    """
    Custom Celery Task base class.
    Automatically updates the Job status in PostgreSQL upon success, failure, or retry.
    This ensures the Database is always the "Source of Truth" for job status.
    """
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
    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.RUNNING.value
            job.started_at = datetime.datetime.utcnow()
            db.commit()

    log_to_db(job_id, "Task started processing.")

    total_steps = duration
    for i in range(total_steps):
        time.sleep(1)
        
        message = f'Processing chunk {i + 1}/{total_steps}...'
        self.update_state(state='PROGRESS', meta={
            'current': i + 1,
            'total': total_steps,
            'message': message,
            'job_id': job_id
        })
        
        if i % max(1, total_steps // 5) == 0:
            log_to_db(job_id, message)
            try:
                result = call_external_service_safely(vector_data, metadata)
                log_to_db(job_id, f"External Service Success: {result['external_id']}")
            except pybreaker.CircuitBreakerError:
                log_to_db(job_id, "External Service Skipped (Circuit Breaker OPEN)", level="WARNING")
            except Exception as e:
                log_to_db(job_id, f"External Service Failed after retries: {str(e)}", level="ERROR")
    
    log_to_db(job_id, "Task processing complete.")

    return {
        "processed_vectors": len(vector_data),
        "status": "indexed",
        "metadata_processed": metadata
    }

@celery_app.task(name="scrape_website", base=DatabaseTask, bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 3})
def scrape_website(self, job_id: str, url: str):
    """
    Scrapes a website and extracts metadata.
    """
    with SessionLocal() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = JobStatus.RUNNING.value
            job.started_at = datetime.datetime.utcnow()
            db.commit()

    log_to_db(job_id, f"Starting scrape for {url}")

    try:
        # Simulate some setup time
        time.sleep(1)
        self.update_state(state='PROGRESS', meta={'message': 'Connecting to site...', 'job_id': job_id})
        
        # 1. Fetch
        log_to_db(job_id, "Sending HTTP GET Request...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 2. Parse
        self.update_state(state='PROGRESS', meta={'message': 'Parsing HTML...', 'job_id': job_id})
        log_to_db(job_id, "Parsing HTML content...")
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Simulate processing time
        time.sleep(2)
        
        # 3. Extract
        title = soup.title.string if soup.title else "No Title"
        description = "No description"
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            description = meta_desc.get("content")
            
        h1_count = len(soup.find_all('h1'))
        links = len(soup.find_all('a'))
        images = len(soup.find_all('img'))
        
        result = {
            "url": url,
            "title": title,
            "description": description,
            "stats": {
                "h1_tags": h1_count,
                "links": links,
                "images": images
            }
        }
        
        log_to_db(job_id, "Scrape complete successfully.")
        return result

    except Exception as e:
        error_msg = f"Scrape failed: {str(e)}"
        log_to_db(job_id, error_msg, level="ERROR")
        # Explicitly fail the task state so the listener catches it
        self.update_state(state='FAILURE', meta={
            'exc_type': type(e).__name__,
            'exc_message': str(e),
            'job_id': job_id
        })
        raise e