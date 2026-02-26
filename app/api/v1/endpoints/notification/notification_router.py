from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.model.notification_model import Notification
from app.model.device_token_model import DeviceToken
from app.model.user_model import User
from app.schemas.notification_schemas import DeviceTokenUpdate, NotificationCreate, NotificationOut, NotificationUpdate
from sqlalchemy.exc import SQLAlchemyError

# 🛡️ Token to user email power dependency
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


@router.post("/device-token")
def save_device_token(
    payload: DeviceTokenUpdate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        existing_for_user = db.query(DeviceToken).filter(DeviceToken.user_id == user.id).first()
        existing_for_token = db.query(DeviceToken).filter(DeviceToken.fcm_token == payload.fcm_token).first()

        if existing_for_token and existing_for_token.user_id != user.id:
            if existing_for_user and existing_for_user.id != existing_for_token.id:
                db.delete(existing_for_user)
            existing_for_token.user_id = user.id
        elif existing_for_user:
            existing_for_user.fcm_token = payload.fcm_token
        else:
            db.add(DeviceToken(user_id=user.id, fcm_token=payload.fcm_token))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save device token")

    return {"message": "Device token saved successfully."}

# 🚀 1. Viewing only own notifications (according to UI design)
@router.get("/", response_model=List[NotificationOut])
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 Token check
):
    # Finding user id with token email
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Returning all user notification list as per design
    return db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc()).all()


# 🚀 2. Marking the notification as "Read" (when the user clicks on 'view details')
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




# 🚀 4. Delete old notifications
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