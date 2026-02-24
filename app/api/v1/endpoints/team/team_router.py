from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.model.team_model import Team
from app.model.user_model import User
from app.model.notification_model import Notification
from app.schemas.team_schemas import TeamCreate, TeamResponse, TeamUpdate

# 🛡️ টোকেন থেকে ইউজার ভেরিফিকেশন করার ডিপেন্ডেন্সি
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/teams",
    tags=["Teams"]
)

# 🚀 ১. নতুন টিম তৈরি করা (মেম্বার ভ্যালিডেশন এবং ওনার ও মেম্বারদের নোটিফিকেশন সহ)
@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    team_data: TeamCreate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    # ওনারকে খুঁজে বের করা
    owner = db.query(User).filter(User.email == current_user_email).first()
    if not owner:
        raise HTTPException(status_code=404, detail="User not found")

    # 🛡️ মেম্বার ভ্যালিডেশন: প্রতিটি ইমেইল সিস্টেমে আছে কি না চেক করা
    member_users = []
    # যদি আপনার Schema-তে members_email লিস্ট থাকে
    if hasattr(team_data, 'members_email') and team_data.members_email:
        for email in team_data.members_email:
            reg_user = db.query(User).filter(User.email == email).first()
            if not reg_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Member email '{email}' is not a registered user. Team creation failed."
                )
            member_users.append(reg_user)

    # নতুন টিম অবজেক্ট তৈরি
    new_team = Team(
        team_name=team_data.team_name,
        description=team_data.description
    )
    
    try:
        db.add(new_team)
        db.commit()
        db.refresh(new_team)

        # 🔔 ১. ওনারের জন্য সাকসেস নোটিফিকেশন পাঠানো
        owner_notification = Notification(
            user_id=owner.id,
            title="Team Created",
            message=f"You have successfully created the team: '{new_team.team_name}'",
            type="team",
            reference_id=new_team.id,
            is_read=False
        )
        db.add(owner_notification)

        # 🔔 ২. প্রতিটি মেম্বারের জন্য নোটিফিকেশন পাঠানো
        for member in member_users:
            member_notification = Notification(
                user_id=member.id,
                title="Added to New Team",
                message=f"You have been added to the team '{new_team.team_name}' by {owner.email}",
                type="team",
                reference_id=new_team.id,
                is_read=False
            )
            db.add(member_notification)

        db.commit() 
        return new_team

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# 🚀 ২. সব টিমের লিস্ট দেখা
@router.get("/", response_model=List[TeamResponse])
def get_all_teams(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    return db.query(Team).all()


# 🚀 ৩. নির্দিষ্ট টিম আপডেট করা
@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: int, 
    team_data: TeamUpdate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    team_query = db.query(Team).filter(Team.id == team_id)
    db_team = team_query.first()

    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")

    update_data = team_data.model_dump(exclude_unset=True)
    
    try:
        team_query.update(update_data, synchronize_session=False)
        db.commit()
        db.refresh(db_team)
        return db_team
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


# 🚀 ৪. টিম ডিলিট করা
@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: int, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    db_team = db.query(Team).filter(Team.id == team_id).first()

    if not db_team:
        raise HTTPException(status_code=404, detail="Team not found")

    try:
        db.delete(db_team)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Delete failed: {str(e)}")