from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt
from typing import Optional

from app.db.database import get_db
from app.model.user_model import User
# 🛡️ টোকেন যাচাইয়ের জন্য আপনার তৈরি করা ইউটিলস ইম্পোর্ট করুন
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 JWT কনফিগারেশন
SECRET_KEY = "your_super_secret_key" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60      # ১ ঘণ্টা
REFRESH_TOKEN_EXPIRE_DAYS = 30        # ৩০ দিন

# -------------------------
# Schemas
# -------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    role: str

# -------------------------
# Helper Functions for Token
# -------------------------
def create_tokens(email: str):
    # ১. Access Token তৈরি
    access_expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({"sub": email, "exp": access_expire}, SECRET_KEY, algorithm=ALGORITHM)
    
    # ২. Refresh Token তৈরি
    refresh_expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = jwt.encode({"sub": email, "exp": refresh_expire}, SECRET_KEY, algorithm=ALGORITHM)
    
    return access_token, refresh_token

# -------------------------
# Login Route (আপনার নিয়ম অনুযায়ী JSON বডি ব্যবহার করে)
# -------------------------

@router.post("/login", response_model=LoginResponse)
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    # ১. ইউজার খুঁজে বের করা
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not pwd_context.verify(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )

    # ২. টোকেন দুটি জেনারেট করা
    access_token, refresh_token = create_tokens(user.email)

    # ৩. ডাটাবেসে রিফ্রেশ টোকেন সেভ করা 🛡️
    user.refresh_token = refresh_token
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not save session")

    # ৪. রেসপন্স পাঠানো
    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role
    }

# -------------------------
# Logout Route (টোকেন চেক সহ নিরাপদ ভার্সন)
# -------------------------

@router.post("/logout")
def logout(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 টোকেন ছাড়া লগআউট করা যাবে না
):
    user = db.query(User).filter(User.email == current_user_email).first()
    if user:
        user.refresh_token = None # 🛡️ সেশনটি চিরতরে বন্ধ করে দেওয়া হলো
        db.commit()
        return {"message": "Logged out successfully"}
    
    raise HTTPException(status_code=404, detail="User not found")