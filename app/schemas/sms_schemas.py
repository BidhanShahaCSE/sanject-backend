from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DirectSmsCreate(BaseModel):
    recipient_email: str
    message: str


class DirectChatRoomEnsureCreate(BaseModel):
    recipient_email: str


class TeamSmsCreate(BaseModel):
    message: str


class SmsMessageOut(BaseModel):
    id: int
    sender_email: str
    recipient_email: Optional[str] = None
    team_id: Optional[int] = None
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class DirectConversationOut(BaseModel):
    id: int
    recipient_email: str
    last_message: str
    created_at: datetime


class DirectChatRoomOut(BaseModel):
    id: int
    recipient_email: str
    created_at: datetime
    existed: bool
