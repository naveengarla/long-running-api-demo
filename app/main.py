from fastapi import FastAPI
from celery.result import AsyncResult
from app.worker import process_vector_data
from app.models import TaskCreate, TaskResponse, TaskStatus

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import asyncio
import json

app = FastAPI(title="Long Running API Demo")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_root():
    return FileResponse('app/static/index.html')

@app.post("/tasks", response_model=TaskResponse, status_code=202)
async def create_task(payload: TaskCreate):
    """
    Submit a long-running task.
    """
    task = process_vector_data.delay(payload.vector_data, payload.metadata, payload.duration)
    return TaskResponse(task_id=task.id, status="Processing")

@app.get("/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Check the status of a task.
    """
    task_result = AsyncResult(task_id)
    
    response = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }

    if task_result.status == 'PROGRESS':
        response["result"] = task_result.result
    elif task_result.ready():
        response["result"] = task_result.result
        
    return response

@app.get("/tasks/{task_id}/stream")
async def stream_task_status(task_id: str):
    """
    Stream task status updates using Server-Sent Events (SSE).
    """
    async def event_generator():
        while True:
            task_result = AsyncResult(task_id)
            
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
