from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List
from datetime import datetime
from app.db.database import get_db
from app.model.reminder_model import Reminder
from app.model.user_model import User  # 🚀 To get User ID
from app.model.notification_model import Notification # 🔔 To send notifications
from app.schemas.reminder_schemas import ReminderCreate, ReminderUpdate, ReminderResponse

# 🛡️ Import the token validation function from your auth file
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email     

router = APIRouter(
    prefix="/reminders",
    tags=["Reminders"]
)


def _cleanup_expired_reminders(db: Session, owner_email: str) -> None:
    now = datetime.now()
    today = now.date()
    current_time = now.time()

    db.query(Reminder).filter(
        Reminder.owner_email == owner_email,
        or_(
            Reminder.reminder_date < today,
            and_(
                Reminder.reminder_date == today,
                Reminder.reminder_time <= current_time,
            ),
        ),
    ).delete(synchronize_session=False)

    db.commit()

# 🚀 1. Creating new reminders (and sending notifications to owners)
@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    reminder_data: ReminderCreate, 
    db: Session = Depends(get_db),
    current_email: str = Depends(get_current_user_email) # 🔒 Access Token check
):
    _cleanup_expired_reminders(db, current_email)

    # Finding user id with token email
    user = db.query(User).filter(User.email == current_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_reminder = Reminder(
        name=reminder_data.name,
        description=reminder_data.description,
        reminder_date=reminder_data.reminder_date,
        reminder_time=reminder_data.reminder_time,
        owner_email=current_email # 🛡️ Using email received from token
    )
    try:
        db.add(new_reminder)
        db.commit()
        db.refresh(new_reminder)

        # 🔔 Sending success notification to owner
        new_notification = Notification(
            user_id=user.id,
            title="Reminder Set",
            message=f"Reminder '{new_reminder.name}' has been set for {new_reminder.reminder_date}.",
            type="reminder",
            reference_id=new_reminder.id,
            is_read=False
        )
        db.add(new_notification)
        db.commit()

        return new_reminder
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 🚀 2. View only your own reminders (filter by Access Token)
@router.get("/", response_model=List[ReminderResponse])
def get_all_reminders(
    db: Session = Depends(get_db),
    current_email: str = Depends(get_current_user_email) # 🔒 Access Token check
):
    _cleanup_expired_reminders(db, current_email)
    return db.query(Reminder).filter(Reminder.owner_email == current_email).all()

# 3. Deleting Reminders (Verifying Ownership with Access Token)
@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: int, 
    db: Session = Depends(get_db),
    current_email: str = Depends(get_current_user_email) # 🔒 Access Token check
):
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id, 
        Reminder.owner_email == current_email
    ).first()

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found or unauthorized")

    try:
        db.delete(reminder)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Delete failed")