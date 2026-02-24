from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.db.database import Base
class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)          # Note name
    description = Column(Text)                    # Short description
    content = Column(Text)                        # Write page content

    owner_email = Column(String, nullable=False)  # Owner

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
