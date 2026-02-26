from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.model.personal_goal_model import PersonalGoal
from app.model.user_model import User  # 🚀 To get User ID
from app.model.notification_model import Notification # 🔔 To send notifications
from app.schemas.personal_goal_schemas import PersonalGoalCreate, PersonalGoalUpdate, PersonalGoalOut

# 🛡️ Import the token validator function you created
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/personal-goals",
    tags=["Personal Goals"]
)

# 🚀 1. Creating New Personal Goals (with Access Token Checks and Notifications)
@router.post("/", response_model=PersonalGoalOut, status_code=status.HTTP_201_CREATED)
def create_personal_goal(
    goal_data: PersonalGoalCreate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 Token check
):
    # Finding user id with token email
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_goal = PersonalGoal(
        title=goal_data.title,
        description=goal_data.description,
        owner_email=current_user_email, 
        is_completed=goal_data.is_completed
    )
    
    try:
        db.add(new_goal)
        db.commit()
        db.refresh(new_goal)

        # 🔔 Sending success notification to owner
        new_notification = Notification(
            user_id=user.id,
            title="Goal Set Successfully",
            message=f"You have set a new personal goal: '{new_goal.title}'",
            type="goal",
            reference_id=new_goal.id,
            is_read=False
        )
        db.add(new_notification)
        db.commit()

        return new_goal
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Creation failed: {str(e)}")

# 🚀 2. View all user goals (filter by Access Token)
@router.get("/", response_model=List[PersonalGoalOut])
def get_personal_goals(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 Token check
):
    return db.query(PersonalGoal).filter(PersonalGoal.owner_email == current_user_email).all()


@router.get("/{goal_id}", response_model=PersonalGoalOut)
def get_personal_goal_by_id(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    goal = db.query(PersonalGoal).filter(
        PersonalGoal.id == goal_id,
        PersonalGoal.owner_email == current_user_email,
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found or unauthorized")
    return goal

# 3. Goal Update (Ownership Verification with Access Token)
@router.patch("/{goal_id}", response_model=PersonalGoalOut)
def update_personal_goal(
    goal_id: int, 
    goal_data: PersonalGoalUpdate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 Token check
):
    goal_query = db.query(PersonalGoal).filter(
        PersonalGoal.id == goal_id, 
        PersonalGoal.owner_email == current_user_email 
    )
    db_goal = goal_query.first()

    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found or unauthorized")

    update_data = goal_data.model_dump(exclude_unset=True)
    
    try:
        goal_query.update(update_data, synchronize_session=False)
        db.commit()
        db.refresh(db_goal)
        return db_goal
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_personal_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    db_goal = db.query(PersonalGoal).filter(
        PersonalGoal.id == goal_id,
        PersonalGoal.owner_email == current_user_email
    ).first()

    if not db_goal:
        raise HTTPException(status_code=404, detail="Goal not found or unauthorized")

    try:
        db.delete(db_goal)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Delete failed: {str(e)}")