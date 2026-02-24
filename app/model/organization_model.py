from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime, ForeignKey
from app.db.database import Base


class Organization(Base):
    __tablename__ = "organizations"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(String, nullable=True)
    org_name = Column(String, nullable=True)
