from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.database import Base

# 🚀 ১. অ্যাসোসিয়েশন টেবিল (টিম এবং ইউজারের মধ্যে সংযোগ তৈরি করবে)
team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True)
)

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    team_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # 🚀 ২. মেম্বারদের সাথে রিলেশনশিপ
    # এটি ব্যবহার করে তুই 'team.members' লিখলে সব মেম্বারের লিস্ট পাবি
    members = relationship("User", secondary=team_members, backref="teams")