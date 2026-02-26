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
    department: str | None = None
    roll: str | None = None
    semester: str | None = None
    batch: str | None = None
    org_id: str | None = None
    org_name: str | None = None


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
            student_required_fields = {
                "department": (data.department or "").strip(),
                "roll": (data.roll or "").strip(),
                "semester": (data.semester or "").strip(),
                "batch": (data.batch or "").strip(),
                "org_id": (data.org_id or "").strip(),
                "org_name": (data.org_name or "").strip(),
            }

            missing_fields = [k for k, v in student_required_fields.items() if not v]
            if missing_fields:
                db.delete(new_user)
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Student profile fields required: {', '.join(missing_fields)}",
                )

            new_profile = Student(
                user_id=new_user.id,
                department=student_required_fields["department"],
                roll=student_required_fields["roll"],
                semester=student_required_fields["semester"],
                batch=student_required_fields["batch"],
                org_id=student_required_fields["org_id"],
                org_name=student_required_fields["org_name"],
            )
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
            # 🛑 If there is any roll outside of these 4, it will throw an error directly
            db.rollback() # Previous user add attempts will be canceled
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{data.role}' is not allowed. Choose student, teacher, manager, employee, or organization."
            )
        # Final commit to save to role specific table
        if data.role in ["student", "teacher", "manager", "employee", "organization"]:
            db.commit()

    except Exception as e:
        # If it fails for some reason, then I will also cancel the user creation
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