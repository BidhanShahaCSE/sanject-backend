from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date


# Shared fields
class TaskBase(BaseModel):
    task_name: str
    description: Optional[str] = None
    start_date: date
    deadline: date
    owner_email: EmailStr
    members_email: Optional[List[EmailStr]] = None


# Create schema
class TaskCreate(TaskBase):
    pass


# Update schema
class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    owner_email: Optional[EmailStr] = None
    members_email: Optional[List[EmailStr]] = None


# Response schema
class TaskResponse(TaskBase):
    id: int

    class Config:
        orm_mode = True   # For SQLAlchemy