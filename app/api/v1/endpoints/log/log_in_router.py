from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from jose import jwt
from typing import Optional

from app.db.database import get_db
from app.model.user_model import User
# 🛡️ Import your created utilities for token verification
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 JWT configuration
SECRET_KEY = "your_super_secret_key" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60      # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30        # 30 days

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


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    user_id: int
    email: EmailStr
    role: str


class MeUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    new_password: Optional[str] = None

# -------------------------
# Helper Functions for Token
# -------------------------
def create_tokens(email: str):
    # 1. Access Token generation
    access_expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt.encode({"sub": email, "exp": access_expire}, SECRET_KEY, algorithm=ALGORITHM)
    
    # 2. Generate Refresh Token
    refresh_expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = jwt.encode({"sub": email, "exp": refresh_expire}, SECRET_KEY, algorithm=ALGORITHM)
    
    return access_token, refresh_token


def create_access_token_only(email: str):
    access_expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": email, "exp": access_expire}, SECRET_KEY, algorithm=ALGORITHM)

# -------------------------
# Login Route (using JSON body according to your rules)
# -------------------------

@router.post("/login", response_model=LoginResponse)
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    # 1. Find users
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not pwd_context.verify(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )

    # 2. Generate two tokens
    access_token, refresh_token = create_tokens(user.email)

    # 3. Saving refresh token in database 🛡️
    user.refresh_token = refresh_token
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Could not save session")

    # 4. Send response
    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role
    }


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_access_token(data: TokenRefreshRequest, db: Session = Depends(get_db)):
    incoming_refresh_token = (data.refresh_token or "").strip()
    if not incoming_refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    try:
        payload = jwt.decode(incoming_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.refresh_token or user.refresh_token != incoming_refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please login again")

    new_access_token = create_access_token_only(user.email)
    return {
        "access_token": new_access_token,
        "refresh_token": incoming_refresh_token,
        "token_type": "bearer",
    }

# -------------------------
# Logout Route (secure version with token check)
# -------------------------

@router.post("/logout")
def logout(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 Cannot logout without token
):
    user = db.query(User).filter(User.email == current_user_email).first()
    if user:
        user.refresh_token = None # 🛡️ The session has been closed permanently
        db.commit()
        return {"message": "Logged out successfully"}
    
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/me", response_model=MeResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }


@router.patch("/me", response_model=MeResponse)
def update_my_profile(
    payload: MeUpdateRequest,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.email is not None:
        new_email = payload.email.strip().lower()
        if new_email != user.email.lower():
            existing = db.query(User).filter(User.email == new_email).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")
            user.email = new_email

    if payload.new_password is not None:
        new_password = payload.new_password.strip()
        if len(new_password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters long",
            )
        user.password = pwd_context.hash(new_password)

    db.commit()
    db.refresh(user)

    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
    }