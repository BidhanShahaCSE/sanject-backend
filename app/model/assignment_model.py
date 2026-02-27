from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.db.database import Base
class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)

    task_type = Column(String, nullable=False)  
    # "Assignment", "Lab Report", "Exam", "Home Work"

    description = Column(Text)

    pdf_link = Column(String)

    start_date = Column(Date)
    deadline = Column(Date)

    org_id = Column(String)
    org_name = Column(String)
    owner_email = Column(String, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)    
