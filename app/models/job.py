"""
SQLAlchemy Data Models.
Defines the database schema for Jobs and Logs.
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import datetime
import enum

class JobStatus(str, enum.Enum):
    """
    Enum representing the lifecycle states of a background job.
    """
    PENDING = "PENDING"     # Created in DB, waiting for worker
    RUNNING = "RUNNING"     # Worker has picked up the task
    SUCCESS = "SUCCESS"     # Task completed successfully
    FAILED = "FAILED"       # Task raised an exception
    CANCELLED = "CANCELLED" # User cancelled the task

class Job(Base):
    """
    Database model for a Background Job.
    Acts as the single source of truth for task status, inputs, and results.
    """
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, default=JobStatus.PENDING.value)
    input_payload = Column(JSON, nullable=True)
    result_payload = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")

class JobLog(Base):
    """
    Detailed log entry for a specific job.
    Used to provide granular progress updates and error details to the user.
    """
    __tablename__ = "job_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"))
    level = Column(String, default="INFO")
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    job = relationship("Job", back_populates="logs")
