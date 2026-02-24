from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.model.reminder_model import Reminder
from app.model.user_model import User  # 🚀 ইউজার আইডি পাওয়ার জন্য
from app.model.notification_model import Notification # 🔔 নোটিফিকেশন পাঠানোর জন্য
from app.schemas.reminder_schemas import ReminderCreate, ReminderUpdate, ReminderResponse

# 🛡️ আপনার auth ফাইল থেকে টোকেন ভ্যালিডেশন ফাংশনটি ইম্পোর্ট করুন
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email     

router = APIRouter(
    prefix="/reminders",
    tags=["Reminders"]
)

# 🚀 ১. নতুন রিমাইন্ডার তৈরি করা (এবং ওনারের কাছে নোটিফিকেশন পাঠানো)
@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    reminder_data: ReminderCreate, 
    db: Session = Depends(get_db),
    current_email: str = Depends(get_current_user_email) # 🔒 Access Token চেক
):
    # টোকেনের ইমেইল দিয়ে ইউজার আইডি খুঁজে বের করা
    user = db.query(User).filter(User.email == current_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_reminder = Reminder(
        name=reminder_data.name,
        description=reminder_data.description,
        reminder_date=reminder_data.reminder_date,
        reminder_time=reminder_data.reminder_time,
        owner_email=current_email # 🛡️ টোকেন থেকে প্রাপ্ত ইমেইল ব্যবহার হচ্ছে
    )
    try:
        db.add(new_reminder)
        db.commit()
        db.refresh(new_reminder)

        # 🔔 ওনারের কাছে সাকসেস নোটিফিকেশন পাঠানো
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

# 🚀 ২. শুধুমাত্র নিজের রিমাইন্ডারগুলো দেখা (Access Token অনুযায়ী ফিল্টার)
@router.get("/", response_model=List[ReminderResponse])
def get_all_reminders(
    db: Session = Depends(get_db),
    current_email: str = Depends(get_current_user_email) # 🔒 Access Token চেক
):
    return db.query(Reminder).filter(Reminder.owner_email == current_email).all()

# 🚀 ৩. রিমাইন্ডার ডিলিট করা (Access Token দিয়ে মালিকানা যাচাই)
@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: int, 
    db: Session = Depends(get_db),
    current_email: str = Depends(get_current_user_email) # 🔒 Access Token চেক
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