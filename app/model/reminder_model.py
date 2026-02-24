from sqlalchemy import Column, Integer, String, Text, Date, Time, DateTime
from datetime import datetime
from app.db.database import Base

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    reminder_date = Column(Date, nullable=False)
    reminder_time = Column(Time, nullable=False) # 🚀 নতুন সময় কলাম
    owner_email = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)