from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime, ForeignKey
from app.db.database import Base

from datetime import datetime, timezone

class AssignmentSubTask(Base):
    __tablename__ = "assignment_subtasks"

    id = Column(Integer, primary_key=True)

    assignment_id = Column(Integer, ForeignKey("assignments.id"))

    name = Column(String, nullable=False)
    description = Column(Text)

    start_date = Column(Date)
    deadline = Column(Date)

    owner_email = Column(String)

    subtask_file = Column(String)   # uploaded file

    created_at = Column(DateTime, default=datetime.utcnow)
