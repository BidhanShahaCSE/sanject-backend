from sqlalchemy import Column, Integer, String, Date, Time, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.db.database import Base

class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)      # DT name
    task_date = Column(Date, nullable=False)  # DD/MM/YYYY

    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    owner_email = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)