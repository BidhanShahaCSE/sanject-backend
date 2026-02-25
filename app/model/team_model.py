from sqlalchemy import Column, Integer, String, Text, ForeignKey
from app.db.database import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)

    team_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)