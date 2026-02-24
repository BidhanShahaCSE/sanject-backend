from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional


class DailyTaskBase(BaseModel):
    name: str
    task_date: date
    start_time: time
    end_time: time
    owner_email: str


class DailyTaskCreate(DailyTaskBase):
    pass


class DailyTaskUpdate(BaseModel):
    name: Optional[str] = None
    task_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class DailyTaskOut(DailyTaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True