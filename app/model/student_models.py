from sqlalchemy import Column, Integer, String,ForeignKey
from app.db.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department = Column(String, nullable=True)
    roll = Column(String, nullable=True)
    semester = Column(String, nullable=True)
    batch = Column(String, nullable=True)

    org_id = Column(String, nullable=True)
    org_name = Column(String, nullable=True)
