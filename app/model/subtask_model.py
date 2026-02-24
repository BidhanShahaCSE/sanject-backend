from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.db.database import Base






class SubTask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True)

    task_id = Column(Integer, ForeignKey("projects.id"))  # link to main task

    title = Column(String, nullable=False)
    description = Column(Text)

    file_path = Column(String)   # uploaded subtask project file
    created_at = Column(DateTime, default=datetime.utcnow)
