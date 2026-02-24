from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from typing import Literal
from app.db.database import get_db
from app.model.employee_model import Employee
from app.model.manager_model import Manager
from app.model.student_models import Student
from app.model.teacher_models import Teacher
from app.model.user_model import User
from app.model.organization_model import Organization

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------
# Schemas
# -------------------------

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # "student", "manager", "employee", "teacher"


class SignUpResponse(BaseModel):
    message: str
    user_id: int
    email: str

    role: Literal["student", "manager", "employee", "teacher", "organization"]
    


# -------------------------
# Sign Up Route
# -------------------------

@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
def signup_user(data: SignUpRequest, db: Session = Depends(get_db)):

    # 1️⃣ Check if user already exists
    existing_user = db.query(User).filter(User.email == data.email).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 2️⃣ Hash the password
    hashed_password = pwd_context.hash(data.password)

    # 3️⃣ Create new user instance
    new_user = User(
        email=data.email,
        password=hashed_password,   
        role=data.role, 
        # Map any other required fields here
    )



    # 4️⃣ Add to DB and commit
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        if data.role == "student":
            new_profile = Student(user_id=new_user.id)
            db.add(new_profile)

        elif data.role == "teacher":
            new_profile = Teacher(user_id=new_user.id)
            db.add(new_profile)

        elif data.role == "manager":
            new_profile = Manager(user_id=new_user.id)
            db.add(new_profile)

        elif data.role == "employee":
            new_profile = Employee(user_id=new_user.id)
            db.add(new_profile)
        elif data.role == "organization":
            new_profile = Organization(user_id=new_user.id)
            db.add(new_profile)


        else:
            # 🛑 যদি এই ৪টির বাইরে কোনো রোল হয়, তবে সরাসরি এরর দেব
            db.rollback() # আগের ইউজার অ্যাড করার চেষ্টা বাতিল করে দেবে
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{data.role}' is not allowed. Choose student, teacher, manager, employee, or organization."
            )
        # রোল স্পেসিফিক টেবিলে সেভ করার জন্য ফাইনাল কমিট
        if data.role in ["student", "teacher", "manager", "employee", "organization"]:
            db.commit()

    except Exception as e:
        # যদি কোনো কারণে ফেইল করে, তাহলে ইউজার ক্রিয়েট হওয়াটাও বাতিল করে দেব
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role profile. Error: {str(e)}"
        )

    
    # 5️⃣ Success response
    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "email": new_user.email,
        "role": new_user.role,
        
    }