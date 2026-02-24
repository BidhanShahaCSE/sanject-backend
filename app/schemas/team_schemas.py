from pydantic import BaseModel
from typing import Optional


# Shared fields
class TeamBase(BaseModel):
    team_name: str
    description: Optional[str] = None


# Used when creating a team (POST)
class TeamCreate(TeamBase):
    pass


# Used when updating a team (PUT / PATCH)
class TeamUpdate(BaseModel):
    team_name: Optional[str] = None
    description: Optional[str] = None


# Used when returning response (GET)
class TeamResponse(TeamBase):
    id: int

    class Config:
        orm_mode = True   # For SQLAlchemy compatibility