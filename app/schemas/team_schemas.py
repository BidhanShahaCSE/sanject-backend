from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


# 🔹 Shared
class TeamBase(BaseModel):
    team_name: str
    description: Optional[str] = None


# 🔹 Create Team (POST)
class TeamCreate(TeamBase):
    members_email: Optional[List[str]] = []   # ✅ ADD THIS


# 🔹 Update Team
class TeamUpdate(BaseModel):
    team_name: Optional[str] = None
    description: Optional[str] = None


# 🔹 Response
class TeamResponse(TeamBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2 (orm_mode এর বদলে)