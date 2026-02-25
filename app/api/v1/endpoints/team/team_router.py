from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app.db.database import get_db
from app.model.team_model import Team
from app.model.user_model import User
from app.model.team_member_model import TeamMember
from app.schemas.team_schemas import TeamCreate, TeamResponse, TeamUpdate
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email

router = APIRouter(
    prefix="/teams",
    tags=["Teams"]
)


# ✅ CREATE TEAM
@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    owner = db.query(User).filter(User.email == current_user_email).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    # 🔹 Validate Members
    member_users = []
    if team_data.members_email:
        for email in team_data.members_email:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(
                    status_code=400,
                    detail=f"{email} is not registered."
                )
            member_users.append(user)

    # 🔹 Create Team
    new_team = Team(
        team_name=team_data.team_name,
        description=team_data.description,
        owner_id=owner.id
    )

    try:
        db.add(new_team)
        db.commit()
        db.refresh(new_team)

        # 🔹 Add Owner to TeamMembers
        db.add(TeamMember(team_id=new_team.id, user_id=owner.id))

        # 🔹 Add Members
        for member in member_users:
            if member.id != owner.id:
                db.add(TeamMember(team_id=new_team.id, user_id=member.id))

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid team data or duplicate member assignment")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create team")

    return new_team


# ✅ GET ALL TEAMS
@router.get("/", response_model=List[TeamResponse])
def get_teams(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    return db.query(Team).all()


# ✅ UPDATE TEAM
@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    team_data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    update_data = team_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(team, key, value)

    db.commit()
    db.refresh(team)

    return team


# ✅ DELETE TEAM
@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    db.delete(team)
    db.commit()

    return None