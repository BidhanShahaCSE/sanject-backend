from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect, text
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


def _ensure_teams_owner_id_column(db: Session) -> None:
    inspector = inspect(db.bind)
    team_columns = {column["name"] for column in inspector.get_columns("teams")}

    if "owner_id" not in team_columns:
        db.execute(text("ALTER TABLE teams ADD COLUMN owner_id INTEGER"))
        db.commit()

    if "created_at" not in team_columns:
        db.execute(text("ALTER TABLE teams ADD COLUMN created_at TIMESTAMP"))
        db.execute(text("UPDATE teams SET created_at = NOW() WHERE created_at IS NULL"))
        db.commit()

    if "updated_at" not in team_columns:
        db.execute(text("ALTER TABLE teams ADD COLUMN updated_at TIMESTAMP"))
        db.execute(text("UPDATE teams SET updated_at = NOW() WHERE updated_at IS NULL"))
        db.commit()


# ✅ CREATE TEAM
@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    try:
        _ensure_teams_owner_id_column(db)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database schema issue: {str(e)}")

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

        db.execute(
            text(
                "UPDATE teams SET created_at = COALESCE(created_at, NOW()), updated_at = COALESCE(updated_at, NOW()) WHERE id = :team_id"
            ),
            {"team_id": new_team.id},
        )
        db.commit()

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
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")

    return new_team


# ✅ GET ALL TEAMS
@router.get("/", response_model=List[TeamResponse])
def get_teams(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    _ensure_teams_owner_id_column(db)
    result = db.execute(
        text(
            "SELECT id, team_name, description, created_at, updated_at FROM teams ORDER BY id DESC"
        )
    )
    return [dict(row) for row in result.mappings().all()]


# ✅ UPDATE TEAM
@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int,
    team_data: TeamUpdate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    _ensure_teams_owner_id_column(db)
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    update_data = team_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(team, key, value)

    db.commit()
    db.execute(
        text("UPDATE teams SET updated_at = NOW() WHERE id = :team_id"),
        {"team_id": team.id},
    )
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
    _ensure_teams_owner_id_column(db)
    team = db.query(Team).filter(Team.id == team_id).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    db.delete(team)
    db.commit()

    return None