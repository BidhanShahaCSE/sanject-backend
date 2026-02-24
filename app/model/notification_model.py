from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.db.database import Base
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, nullable=False)  # who receives notification

    title = Column(String, nullable=False)     # Project Title / Team Title
    message = Column(Text, nullable=False)     # assigned as manager etc.

    type = Column(String)  # "project", "team", "goal"

    reference_id = Column(Integer)  
    # project_id / team_id / goal_id (optional use)

    is_read = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
