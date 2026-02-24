from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.db.database import Base
class PersonalGoal(Base):
    __tablename__ = "personal_goals"

    id = Column(Integer, primary_key=True)

    title = Column(String, nullable=False)
    description = Column(Text)

    owner_email = Column(String, nullable=False)

    is_completed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
