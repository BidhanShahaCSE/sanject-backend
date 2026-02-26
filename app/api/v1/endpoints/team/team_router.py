from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect, text
from typing import List

from app.db.database import get_db
from app.model.team_model import Team
from app.model.user_model import User
from app.model.team_member_model import TeamMember
from app.model.notification_model import Notification
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

        db.add(
            Notification(
                user_id=owner.id,
                title="Team Created",
                message=f"You created team '{new_team.team_name}'",
                type="team",
                reference_id=new_team.id,
                is_read=False,
            )
        )

        for member in member_users:
            if member.id == owner.id:
                continue
            db.add(
                Notification(
                    user_id=member.id,
                    title="Added to Team",
                    message=f"You were added to team '{new_team.team_name}' by {owner.email}",
                    type="team",
                    reference_id=new_team.id,
                    is_read=False,
                )
            )

        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Invalid team data or duplicate member assignment")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")

    member_emails = [owner.email] + [m.email for m in member_users if m.id != owner.id]
    return {
        "id": new_team.id,
        "team_name": new_team.team_name,
        "description": new_team.description,
        "members_email": member_emails,
        "created_at": db.execute(
            text("SELECT created_at FROM teams WHERE id = :team_id"),
            {"team_id": new_team.id},
        ).scalar(),
        "updated_at": db.execute(
            text("SELECT updated_at FROM teams WHERE id = :team_id"),
            {"team_id": new_team.id},
        ).scalar(),
    }


# ✅ GET ALL TEAMS
@router.get("/", response_model=List[TeamResponse])
def get_teams(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    _ensure_teams_owner_id_column(db)
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    team_id_rows = db.query(TeamMember.team_id).filter(TeamMember.user_id == user.id).all()
    my_team_ids = [row[0] for row in team_id_rows]
    if not my_team_ids:
        return []

    teams_query = db.query(Team).filter(Team.id.in_(my_team_ids)).order_by(Team.id.desc()).all()

    teams = []
    for team in teams_query:
        row = db.execute(
            text("SELECT created_at, updated_at FROM teams WHERE id = :team_id"),
            {"team_id": team.id},
        ).mappings().first()
        teams.append(
            {
                "id": team.id,
                "team_name": team.team_name,
                "description": team.description,
                "created_at": row["created_at"] if row else None,
                "updated_at": row["updated_at"] if row else None,
            }
        )

    user_rows = db.execute(text("SELECT id, email FROM users")).mappings().all()
    user_email_by_id = {row["id"]: row["email"] for row in user_rows}

    member_rows = db.execute(
        text("SELECT team_id, user_id FROM team_members")
    ).mappings().all()

    members_by_team = {}
    for row in member_rows:
        team_id = row["team_id"]
        user_id = row["user_id"]
        email = user_email_by_id.get(user_id)
        if not email:
            continue
        members_by_team.setdefault(team_id, []).append(email)

    for item in teams:
        item["members_email"] = members_by_team.get(item["id"], [])

    return teams


@router.get("/{team_id}", response_model=TeamResponse)
def get_team_by_id(
    team_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    _ensure_teams_owner_id_column(db)

    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    member_row = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user.id,
    ).first()
    if not member_row:
        raise HTTPException(status_code=404, detail="Team not found")

    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    member_ids = db.query(TeamMember.user_id).filter(TeamMember.team_id == team_id).all()
    member_ids = [row[0] for row in member_ids]
    member_emails = []
    if member_ids:
        members = db.query(User.email).filter(User.id.in_(member_ids)).all()
        member_emails = [row[0] for row in members]

    return {
        "id": team.id,
        "team_name": team.team_name,
        "description": team.description,
        "members_email": member_emails,
        "created_at": db.execute(
            text("SELECT created_at FROM teams WHERE id = :team_id"),
            {"team_id": team.id},
        ).scalar(),
        "updated_at": db.execute(
            text("SELECT updated_at FROM teams WHERE id = :team_id"),
            {"team_id": team.id},
        ).scalar(),
    }


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

    if team.owner_id is not None:
        owner = db.query(User).filter(User.id == team.owner_id).first()
        if owner and owner.email != current_user_email:
            raise HTTPException(status_code=403, detail="Only team owner can edit team")

    update_data = team_data.model_dump(exclude_unset=True)
    members_email = update_data.pop("members_email", None)

    for key, value in update_data.items():
        setattr(team, key, value)

    if members_email is not None:
        existing_users = db.query(User).filter(User.email.in_(members_email)).all()
        existing_emails = {u.email for u in existing_users}
        missing = [email for email in members_email if email not in existing_emails]
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"These members are not registered: {', '.join(missing)}",
            )

        owner_member = db.query(TeamMember).filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id == team.owner_id,
        ).first()
        if not owner_member:
            db.add(TeamMember(team_id=team.id, user_id=team.owner_id))
            db.flush()

        db.query(TeamMember).filter(
            TeamMember.team_id == team.id,
            TeamMember.user_id != team.owner_id,
        ).delete(synchronize_session=False)

        for user in existing_users:
            if user.id == team.owner_id:
                continue
            db.add(TeamMember(team_id=team.id, user_id=user.id))

    db.commit()
    db.execute(
        text("UPDATE teams SET updated_at = NOW() WHERE id = :team_id"),
        {"team_id": team.id},
    )
    db.commit()
    db.refresh(team)

    member_ids = db.query(TeamMember.user_id).filter(TeamMember.team_id == team.id).all()
    member_ids = [row[0] for row in member_ids]
    member_emails = []
    if member_ids:
        members = db.query(User.email).filter(User.id.in_(member_ids)).all()
        member_emails = [row[0] for row in members]

    return {
        "id": team.id,
        "team_name": team.team_name,
        "description": team.description,
        "members_email": member_emails,
        "created_at": db.execute(
            text("SELECT created_at FROM teams WHERE id = :team_id"),
            {"team_id": team.id},
        ).scalar(),
        "updated_at": db.execute(
            text("SELECT updated_at FROM teams WHERE id = :team_id"),
            {"team_id": team.id},
        ).scalar(),
    }


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

    if team.owner_id is not None:
        owner = db.query(User).filter(User.id == team.owner_id).first()
        if owner and owner.email != current_user_email:
            raise HTTPException(status_code=403, detail="Only team owner can delete team")

    db.query(TeamMember).filter(TeamMember.team_id == team_id).delete(synchronize_session=False)
    db.delete(team)
    db.commit()

    return None