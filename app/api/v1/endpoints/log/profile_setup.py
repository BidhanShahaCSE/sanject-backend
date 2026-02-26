from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.model.user_model import User
from app.model.student_models import Student
from app.model.teacher_models import Teacher
from app.model.manager_model import Manager
from app.model.employee_model import Employee
from app.model.organization_model import Organization

from app.schemas.student_schemas import StudentCreate
from app.schemas.teacher_schemas import TeacherCreate
from app.schemas.manager_schemas import ManagerCreate
from app.schemas.employee_schemas import EmployeeCreate
from app.schemas.organization_schemas import OrganizationCreate

from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(prefix="/profile", tags=["Profile Setup"])

# 🛡️ Common functions: roll check and data synchronization
def secure_profile_sync(db: Session, email: str, target_role: str, model, data_dict: dict, profile_name: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 🚨 Role Validation: User with wrong role will get error if they enter wrong endpoint
    if user.role.lower() != target_role.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Forbidden: Your role is '{user.role}', cannot access '{target_role}' setup."
        )

    # Update username (name from setup page)
    user.name = profile_name

    # Duplicate Fix: Updating previous row without creating new row
    existing = db.query(model).filter(model.user_id == user.id).first()
    
    if existing:
        for key, value in data_dict.items():
            setattr(existing, key, value)
    else:
        new_obj = model(user_id=user.id, **data_dict)
        db.add(new_obj)
    
    try:
        db.commit()
        return {"status": "success", "message": f"{target_role.capitalize()} profile synchronized"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 🚀 1. Student profile setup
@router.post("/setup/student")
def setup_student(profile_name: str, data: StudentCreate, db: Session = Depends(get_db), email: str = Depends(get_current_user_email)):
    return secure_profile_sync(db, email, "student", Student, data.model_dump(), profile_name)

# 🚀 2. Teacher profile setup
@router.post("/setup/teacher")
def setup_teacher(profile_name: str, data: TeacherCreate, db: Session = Depends(get_db), email: str = Depends(get_current_user_email)):
    return secure_profile_sync(db, email, "teacher", Teacher, data.model_dump(), profile_name)

# 3. Manager profile setup
@router.post("/setup/manager")
def setup_manager(profile_name: str, data: ManagerCreate, db: Session = Depends(get_db), email: str = Depends(get_current_user_email)):
    return secure_profile_sync(db, email, "manager", Manager, data.model_dump(), profile_name)

# 🚀 4. Employee profile setup
@router.post("/setup/employee")
def setup_employee(profile_name: str, data: EmployeeCreate, db: Session = Depends(get_db), email: str = Depends(get_current_user_email)):
    return secure_profile_sync(db, email, "employee", Employee, data.model_dump(), profile_name)

# 5. Organization profile setup
@router.post("/setup/organization")
def setup_org(profile_name: str, data: OrganizationCreate, db: Session = Depends(get_db), email: str = Depends(get_current_user_email)):
    return secure_profile_sync(db, email, "organization", Organization, data.model_dump(), profile_name)