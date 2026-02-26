from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import List, Optional  # 👈 Make sure to import Optional

# To take input from the user (all required)
class ProjectCreate(BaseModel):
    project_name: str
    description: str
    start_date: date
    deadline: date
    owner_email: EmailStr
    members_email: List[EmailStr]

# 🚀 To update the project (all fields are optional)
class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    members_email: Optional[List[EmailStr]] = None

# To send output from the database
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