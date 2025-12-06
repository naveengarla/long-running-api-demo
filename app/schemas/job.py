"""
Pydantic Schemas.
Defines the request and response structures for the API.
These schemas handle data validation and serialization.
"""
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

class TaskType(str, Enum):
    """Supported task types for dispatching."""
    VECTOR = "vector_processing"
    SCRAPE = "web_scrape"

class TaskCreate(BaseModel):
    """
    Payload for creating a new task.
    Supports both Vector Processing and Web Scraping.
    """
    vector_data: Optional[List[float]] = None # For VECTOR tasks
    metadata: dict
    duration: int = 10
    url: Optional[str] = None # For SCRAPE tasks
    task_type: TaskType = TaskType.VECTOR

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
    """
    Full details of a job, including status, results, and execution logs.
    """
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
