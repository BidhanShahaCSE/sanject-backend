from pydantic import BaseModel, EmailStr
from datetime import date
from typing import List

class MemberUpdateDetails(BaseModel):
    member_email: EmailStr
    role: str
    description: str
    start_date: date
    deadline: date

class ProjectMembersUpdateList(BaseModel):
    members: List[MemberUpdateDetails] # 👈 It will take multiple members in list form