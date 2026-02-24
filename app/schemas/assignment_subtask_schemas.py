from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class AssignmentSubTaskBase(BaseModel):
    assignment_id: int
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    owner_email: Optional[str] = None
    subtask_file: Optional[str] = None


class AssignmentSubTaskCreate(AssignmentSubTaskBase):
    pass


class AssignmentSubTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    owner_email: Optional[str] = None
    subtask_file: Optional[str] = None


class AssignmentSubTaskOut(AssignmentSubTaskBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True