from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from app.db.database import Base

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    joining_year = Column(Integer, nullable=True)

    org_id = Column(String, nullable=True)
    org_name = Column(String, nullable=True)
