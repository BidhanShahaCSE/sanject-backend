from sqlalchemy import Column, DateTime, Integer, String
from datetime import datetime

from app.db.database import Base


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    fcm_token = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
