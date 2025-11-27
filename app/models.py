from pydantic import BaseModel
from typing import Optional, Any

class TaskCreate(BaseModel):
    # Example payload for a vector DB operation
    vector_data: list[float]
    metadata: dict[str, Any]
    duration: Optional[int] = 10

class TaskResponse(BaseModel):
    task_id: str
    status: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
