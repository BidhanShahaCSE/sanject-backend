from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from app.db.database import Base


class AssignmentSubtaskNoteLink(Base):
    __tablename__ = "assignment_subtask_note_links"

    id = Column(Integer, primary_key=True)
    subtask_id = Column(Integer, ForeignKey("assignment_subtasks.id"), nullable=False, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False, index=True)
    owner_email = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
