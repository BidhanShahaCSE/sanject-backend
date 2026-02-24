from sqlalchemy import Column, Integer, String, Date, Text
from app.db.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    task_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    start_date = Column(Date, nullable=False)
    deadline = Column(Date, nullable=False)

    owner_email = Column(String, nullable=False)

    # Multiple emails stored as comma-separated string
    members_email = Column(Text, nullable=True)
