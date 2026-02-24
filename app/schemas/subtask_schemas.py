from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Shared fields
class SubTaskBase(BaseModel):
    task_id: int
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None


# Create schema
class SubTaskCreate(SubTaskBase):
    pass


# Update schema
class SubTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    file_path: Optional[str] = None


# Response schema
class SubTaskResponse(SubTaskBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True   # For SQLAlchemy