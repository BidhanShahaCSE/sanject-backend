from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from app.db.database import Base

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    content = Column(Text, nullable=True)

    owner_email = Column(String, nullable=False, index=True)  # login user
    member_emails = Column(Text, nullable=True)  # other members (comma separated)

    created_at = Column(DateTime, default=datetime.utcnow)