from fastapi import APIRouter
from app.api.endpoints import tasks

api_router = APIRouter()
api_router.include_router(tasks.router, tags=["tasks"])
