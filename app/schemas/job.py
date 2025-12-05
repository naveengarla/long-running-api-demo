from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class TaskCreate(BaseModel):
    vector_data: List[float]
    metadata: dict
    duration: int = 10

class TaskResponse(BaseModel):
    task_id: str
    status: str

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str

    class Config:
        from_attributes = True

class TaskStatusResponse(BaseModel):
    id: str = Field(..., serialization_alias="task_id")
    status: str
    result_payload: Optional[Any] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    logs: List[LogEntry] = []

    class Config:
        from_attributes = True
