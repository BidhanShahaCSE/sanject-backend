from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime, ForeignKey

from app.db.database import Base
# app/model/project_member_model.py
class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    
    # 🚀 এই কলামটি যোগ করুন, যা মিসিং ছিল
    email = Column(String, nullable=False) 
    
    role = Column(String, nullable=True) # Role ঐচ্ছিক হতে পারে
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    deadline = Column(Date, nullable=False)