from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from app.db.database import Base


class DirectChatRoom(Base):
    __tablename__ = "direct_chat_rooms"
    __table_args__ = (
        UniqueConstraint("participant_one", "participant_two", name="uq_direct_chat_pair"),
    )

    id = Column(Integer, primary_key=True, index=True)
    participant_one = Column(String, nullable=False, index=True)
    participant_two = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
