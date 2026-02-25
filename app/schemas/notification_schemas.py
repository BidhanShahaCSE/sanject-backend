from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationBase(BaseModel):
    user_id: int
    title: str
    message: str
    type: Optional[str] = None
    reference_id: Optional[int] = None
    is_read: Optional[bool] = False


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None


class DeviceTokenUpdate(BaseModel):
    fcm_token: str


class NotificationOut(NotificationBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True