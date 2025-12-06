from celery import Celery
from app.core.config import settings
from app.core.telemetry import init_tracer, instrument_celery
import os

# Initialize Tracer for Worker if this file is loaded by the worker process
# A simple heuristic: check if we are in a worker context or if env var is set
if os.getenv("OTEL_SERVICE_NAME") == "worker-service":
    init_tracer("worker-service")
    instrument_celery(None) # app argument is optional for auto-instrumentation

celery_app = Celery(
    "worker", 
    broker=settings.CELERY_BROKER_URL, 
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Reliability Settings:
    task_acks_late=True, # Task is ACKed only AFTER execution. Prevents data loss if worker crashes.
    task_reject_on_worker_lost=True, # Re-queue task if worker process is killed abruptly (OOM).
    broker_transport_options={"visibility_timeout": 3600}, # 1 hour visibility timeout. If worker doesn't ACK in 1h, task is re-queued.
)
