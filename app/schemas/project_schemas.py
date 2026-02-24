from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import List, Optional  # 👈 Optional ইম্পোর্ট করা নিশ্চিত করুন

# ইউজার থেকে ইনপুট নেওয়ার জন্য (সব আবশ্যিক)
class ProjectCreate(BaseModel):
    project_name: str
    description: str
    start_date: date
    deadline: date
    owner_email: EmailStr
    members_email: List[EmailStr]

# 🚀 প্রজেক্ট আপডেট করার জন্য (সব ফিল্ড ঐচ্ছিক/Optional)
class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    members_email: Optional[List[EmailStr]] = None

# ডাটাবেস থেকে আউটপুট পাঠানোর জন্য
class ProjectResponse(BaseModel):
    id: int
    project_name: str
    description: str
    start_date: date
    deadline: date
    owner_id: int
    owner_email: str
    members_email: str 
    created_at: datetime

    class Config:
        from_attributes = True