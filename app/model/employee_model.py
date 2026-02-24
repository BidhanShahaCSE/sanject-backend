from sqlalchemy import Column, ForeignKey, Integer, String
from app.db.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    employee_id = Column(String, nullable=True, unique=True)
    joining_year = Column(Integer, nullable=True)

    org_id = Column(String, nullable=True)
    org_name = Column(String, nullable=True)