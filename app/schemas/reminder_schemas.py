from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, time, datetime

class ReminderBase(BaseModel):
    name: str
    description: Optional[str] = None
    reminder_date: date
    reminder_time: time # 🚀 Added time
    owner_email: EmailStr

class ReminderCreate(ReminderBase):
    pass

class ReminderUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    reminder_date: Optional[date] = None
    reminder_time: Optional[time] = None

class ReminderResponse(ReminderBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True