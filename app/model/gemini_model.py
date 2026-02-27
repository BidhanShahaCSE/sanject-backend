from sqlalchemy import Column, Integer, Text, String, DateTime
from app.db.database import Base
import datetime

class GeminiChat(Base):
    __tablename__ = "gemini_chats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True) # ইউজারের রেফারেন্স রাখার জন্য
    prompt = Column(Text)
    ai_response = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)