from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, String

from app.db.database import Base


class ProjectChatMessage(Base):
    __tablename__ = "project_chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    sender_email = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
