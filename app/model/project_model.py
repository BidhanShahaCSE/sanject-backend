from sqlalchemy import Column, DateTime, Integer, String, Date, Text, func
from app.db.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)

    project_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    start_date = Column(Date, nullable=False)
    deadline = Column(Date, nullable=False)

    owner_email = Column(String, nullable=False)
    owner_id = Column(Integer, nullable=False)
    # Store multiple emails as comma-separated string
    members_email = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())