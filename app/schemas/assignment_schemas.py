from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class AssignmentBase(BaseModel):
    task_type: str
    description: Optional[str] = None
    pdf_link: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    org_id: Optional[str] = None
    org_name: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    task_type: Optional[str] = None
    description: Optional[str] = None
    pdf_link: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    org_id: Optional[str] = None
    org_name: Optional[str] = None


class AssignmentOut(AssignmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True