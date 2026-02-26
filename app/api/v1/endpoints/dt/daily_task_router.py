from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.model.daily_task_model import DailyTask
from app.model.user_model import User
from app.model.notification_model import Notification
from app.schemas.daily_task_schemas import DailyTaskCreate, DailyTaskOut, DailyTaskUpdate

# 🛡️ Token to User Verification
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(tags=["Daily Tasks"])

# 🚀 1. Creating a new Daily Task
@router.post("/daily-tasks/", response_model=DailyTaskOut, status_code=status.HTTP_201_CREATED)
@router.post("/dt/", response_model=DailyTaskOut, status_code=status.HTTP_201_CREATED)
def create_daily_task(
    task_data: DailyTaskCreate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_task = DailyTask(
        name=task_data.name,
        task_date=task_data.task_date,
        start_time=task_data.start_time,
        end_time=task_data.end_time,
        owner_email=current_user_email
    )
    
    try:
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        # 🔔 Notification sending
        new_notification = Notification(
            user_id=user.id,
            title="Task Created Successfully",
            message=f"Your daily task '{new_task.name}' has been scheduled for {new_task.task_date}.",
            type="daily_task",
            reference_id=new_task.id,
            is_read=False
        )
        db.add(new_notification)
        db.commit()

        return new_task
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# 🚀 2. View a list of all the user's daily tasks
@router.get("/daily-tasks/", response_model=List[DailyTaskOut])
@router.get("/dt/", response_model=List[DailyTaskOut])
def get_my_daily_tasks(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    return db.query(DailyTask).filter(
        DailyTask.owner_email == current_user_email
    ).order_by(DailyTask.task_date.desc()).all()


# 3. Updating specific tasks (including all fields)
@router.patch("/daily-tasks/{task_id}", response_model=DailyTaskOut)
@router.patch("/dt/{task_id}", response_model=DailyTaskOut)
def update_daily_task(
    task_id: int, 
    task_data: DailyTaskUpdate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    task_query = db.query(DailyTask).filter(DailyTask.id == task_id, DailyTask.owner_email == current_user_email)
    db_task = task_query.first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")

    # 🚀 If exclude_unset=True, only the fields sent by the user will be updated
    update_data = task_data.model_dump(exclude_unset=True)
    
    try:
        task_query.update(update_data, synchronize_session=False)
        db.commit()
        db.refresh(db_task)
        return db_task
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


# 🚀 4. Deleting Daily Tasks
@router.delete("/daily-tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/dt/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_daily_task(
    task_id: int, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    db_task = db.query(DailyTask).filter(DailyTask.id == task_id, DailyTask.owner_email == current_user_email).first()

    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found or unauthorized")

    try:
        db.delete(db_task)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Delete failed: {str(e)}")