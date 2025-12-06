from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from celery.result import AsyncResult
from app.worker import process_vector_data, celery_app
from app.schemas.job import TaskCreate, TaskResponse, TaskStatusResponse, LogEntry
from app.core.database import get_db
from app.models.job import Job, JobLog, JobStatus
from fastapi.responses import StreamingResponse
import asyncio
import json
import datetime

router = APIRouter()

@router.post("/tasks", response_model=TaskResponse, status_code=202)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)):
    """
    Submit a long-running task and persist it to the database.
    """
    # Create Job record
    new_job = Job(
        input_payload=payload.dict(),
        status=JobStatus.PENDING.value
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    # Trigger Celery Task based on Type
    if payload.task_type == "web_scrape":
        task = celery_app.send_task(
            "scrape_website",
            args=[new_job.id, payload.url],
            task_id=new_job.id
        )
    else:
        # Default to Vector Processing
        task = process_vector_data.apply_async(
            args=[new_job.id, payload.vector_data, payload.metadata, payload.duration],
            task_id=new_job.id
        )

    return TaskResponse(task_id=new_job.id, status="Processing")

@router.get("/tasks", response_model=list[TaskStatusResponse])
async def list_tasks(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    """
    List all jobs with pagination.
    """
    result = await db.execute(select(Job).offset(skip).limit(limit).order_by(Job.created_at.desc()))
    jobs = result.scalars().all()
    return jobs

@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the status and details of a specific job from the database.
    """
    result = await db.execute(select(Job).options(selectinload(Job.logs)).where(Job.id == task_id))
    job = result.scalars().first()

    if not job:
        raise HTTPException(status_code=404, detail="Task not found")

    return job

@router.get("/tasks/{task_id}/logs", response_model=list[LogEntry])
async def get_task_logs(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Retrieve logs for a specific job.
    """
    result = await db.execute(select(JobLog).where(JobLog.job_id == task_id).order_by(JobLog.timestamp))
    logs = result.scalars().all()
    return logs

@router.delete("/tasks/{task_id}", status_code=204)
async def cancel_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Cancel a running task.
    """
    result = await db.execute(select(Job).where(Job.id == task_id))
    job = result.scalars().first()

    if not job:
        raise HTTPException(status_code=404, detail="Task not found")

    # Revoke Celery task
    celery_app.control.revoke(task_id, terminate=True)

    # Update DB status
    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.datetime.utcnow()
    await db.commit()

    return

@router.get("/tasks/{task_id}/stream")
async def stream_task_status(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    Stream task status updates using Server-Sent Events (SSE).
    """
    async def event_generator():
        while True:
            task_result = celery_app.AsyncResult(task_id)
            
            data = {
                "task_id": task_id,
                "status": task_result.status,
                "result": None
            }

            if task_result.status == 'PROGRESS':
                data["result"] = task_result.result
            elif task_result.ready():
                data["result"] = task_result.result
            
            yield f"data: {json.dumps(data)}\n\n"

            if task_result.ready():
                break
            
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
