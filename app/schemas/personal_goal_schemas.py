from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PersonalGoalBase(BaseModel):
    title: str
    description: Optional[str] = None
    owner_email: str
    is_completed: Optional[bool] = False


class PersonalGoalCreate(PersonalGoalBase):
    pass


class PersonalGoalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None


class PersonalGoalOut(PersonalGoalBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True