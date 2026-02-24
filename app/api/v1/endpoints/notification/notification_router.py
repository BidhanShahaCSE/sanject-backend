from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.model.notification_model import Notification
from app.model.user_model import User
from app.schemas.notification_schemas import NotificationCreate, NotificationOut, NotificationUpdate

# 🛡️ টোকেন থেকে ইউজার ইমেইল পাওয়ার ডিপেন্ডেন্সি
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)

# 🚀 ১. শুধুমাত্র নিজের নোটিফিকেশনগুলো দেখা (UI ডিজাইন অনুযায়ী)
@router.get("/", response_model=List[NotificationOut])
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 টোকেন চেক
):
    # টোকেনের ইমেইল দিয়ে ইউজার আইডি খুঁজে বের করা
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # ডিজাইন অনুযায়ী ইউজারের সব নোটিফিকেশন লিস্ট রিটার্ন করা
    return db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).all()


# 🚀 ২. নোটিফিকেশন "Read" হিসেবে মার্ক করা (যখন ইউজার 'view details' এ ক্লিক করবে)
@router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    user = db.query(User).filter(User.email == current_user_email).first()
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id, 
        Notification.user_id == user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification




# 🚀 ৪. পুরনো নোটিফিকেশন ডিলিট করা
@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    user = db.query(User).filter(User.email == current_user_email).first()
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id, 
        Notification.user_id == user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()
    return None