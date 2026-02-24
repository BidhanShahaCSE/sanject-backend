from sqlalchemy import Column, ForeignKey, Integer, String
from app.db.database import Base


class Manager(Base):
    __tablename__ = "managers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    joining_year = Column(Integer, nullable=True)

    org_id = Column(String, nullable=True)
    org_name = Column(String, nullable=True)
