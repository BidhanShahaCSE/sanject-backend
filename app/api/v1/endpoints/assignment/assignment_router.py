from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.model.assignment_model import Assignment
from app.model.assignment_subtask_model import AssignmentSubTask
from app.model.user_model import User
from app.model.project_model import Project 
from app.model.project_member_model import ProjectMember 
from app.model.notification_model import Notification
from app.schemas.assignment_schemas import AssignmentCreate, AssignmentOut, AssignmentUpdate
from app.schemas.assignment_subtask_schemas import AssignmentSubTaskCreate, AssignmentSubTaskOut, AssignmentSubTaskUpdate

from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/assignments",
    tags=["Assignments & SubTasks"]
)

ALLOWED_TASK_TYPES = ["Assignment", "Lab Report", "Exam", "Home Work"]

# ----------------------------------------------------------------
# 🚀 ১. মেইন অ্যাসাইনমেন্ট সেকশন
# ----------------------------------------------------------------

@router.post("/", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def create_assignment(
    data: AssignmentCreate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    if data.task_type not in ALLOWED_TASK_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid task type. Allowed: {ALLOWED_TASK_TYPES}")

    owner = db.query(User).filter(User.email == current_user_email).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    new_assignment = Assignment(
        task_type=data.task_type,
        description=data.description,
        pdf_link=data.pdf_link,
        start_date=data.start_date,
        deadline=data.deadline,
        org_id=data.org_id,
        org_name=data.org_name
    )
    
    try:
        db.add(new_assignment)
        db.commit()
        db.refresh(new_assignment)

        owner_notification = Notification(
            user_id=owner.id,
            title="Assignment Created",
            message=f"You successfully created {new_assignment.task_type}: '{new_assignment.org_name}'",
            type="assignment",
            reference_id=new_assignment.id,
            is_read=False
        )
        db.add(owner_notification)

        if new_assignment.org_id:
            org_members = db.query(ProjectMember).filter(ProjectMember.project_id == new_assignment.org_id).all()
            for member_entry in org_members:
                member_user = db.query(User).filter(User.email == member_entry.email).first()
                if member_user and member_user.id != owner.id:
                    member_notification = Notification(
                        user_id=member_user.id,
                        title=f"New {new_assignment.task_type}",
                        message=f"A new {new_assignment.task_type} posted in '{new_assignment.org_name}' by {owner.email}",
                        type="assignment",
                        reference_id=new_assignment.id,
                        is_read=False
                    )
                    db.add(member_notification)

        db.commit() 
        return new_assignment
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------
# 🚀 ২. সাব-টাস্ক সেকশন (Upload, Update, Delete & Notifications)
# ----------------------------------------------------------------

@router.post("/subtasks/upload-file", response_model=AssignmentSubTaskOut)
def upload_subtask_file(
    data: AssignmentSubTaskCreate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    user = db.query(User).filter(User.email == current_user_email).first()
    
    new_subtask = AssignmentSubTask(
        assignment_id=data.assignment_id,
        name=data.name,
        description=data.description,
        start_date=data.start_date,
        deadline=data.deadline,
        owner_email=current_user_email,
        subtask_file=data.subtask_file
    )
    
    try:
        db.add(new_subtask)
        db.commit()
        db.refresh(new_subtask)

        member_notif = Notification(
            user_id=user.id,
            title="File Uploaded",
            message=f"File uploaded for subtask: '{new_subtask.name}'",
            type="assignment",
            reference_id=new_subtask.id,
            is_read=False
        )
        db.add(member_notif)
        db.commit()
        return new_subtask
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 🚀 সাব-টাস্ক আপডেট করা
@router.patch("/subtasks/{subtask_id}", response_model=AssignmentSubTaskOut)
def update_subtask(
    subtask_id: int,
    data: AssignmentSubTaskUpdate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    subtask_query = db.query(AssignmentSubTask).filter(
        AssignmentSubTask.id == subtask_id, 
        AssignmentSubTask.owner_email == current_user_email # 🛡️ মালিকানা যাচাই
    )
    db_subtask = subtask_query.first()

    if not db_subtask:
        raise HTTPException(status_code=404, detail="Subtask not found or unauthorized")

    update_data = data.model_dump(exclude_unset=True)
    
    try:
        subtask_query.update(update_data, synchronize_session=False)
        db.commit()
        db.refresh(db_subtask)
        return db_subtask
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

# 🚀 সাব-টাস্ক ডিলিট করা
@router.delete("/subtasks/{subtask_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subtask(
    subtask_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    db_subtask = db.query(AssignmentSubTask).filter(
        AssignmentSubTask.id == subtask_id, 
        AssignmentSubTask.owner_email == current_user_email # 🛡️ মালিকানা যাচাই
    ).first()

    if not db_subtask:
        raise HTTPException(status_code=404, detail="Subtask not found or unauthorized")

    try:
        db.delete(db_subtask)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

# ----------------------------------------------------------------
# 🚀 ৩. সাবমিশন এবং ইস্যু রিপোর্টিং
# ----------------------------------------------------------------

@router.post("/subtasks/{subtask_id}/complete-submission")
def full_submission_notification(
    subtask_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    subtask = db.query(AssignmentSubTask).filter(AssignmentSubTask.id == subtask_id).first()
    main_assignment = db.query(Assignment).filter(Assignment.id == subtask.assignment_id).first()
    project = db.query(Project).filter(Project.id == main_assignment.org_id).first()
    
    member = db.query(User).filter(User.email == current_user_email).first()
    owner = db.query(User).filter(User.id == project.owner_id).first()

    try:
        db.add(Notification(user_id=member.id, title="Task Submitted", message=f"Subtask '{subtask.name}' submitted.", type="assignment", reference_id=subtask.id))
        db.add(Notification(user_id=owner.id, title="Subtask Received", message=f"{member.email} submitted '{subtask.name}'", type="assignment", reference_id=subtask.id))
        db.commit()
        return {"message": "Notifications sent."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subtasks/{subtask_id}/report-issue")
def report_subtask_issue(
    subtask_id: int,
    issue_note: str,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    subtask = db.query(AssignmentSubTask).filter(AssignmentSubTask.id == subtask_id).first()
    main_assignment = db.query(Assignment).filter(Assignment.id == subtask.assignment_id).first()
    project = db.query(Project).filter(Project.id == main_assignment.org_id).first()
    owner = db.query(User).filter(User.id == project.owner_id).first()

    try:
        problem_notif = Notification(
            user_id=owner.id,
            title="Problem Reported",
            message=f"Issue in '{subtask.name}' by {current_user_email}: {issue_note}",
            type="assignment",
            reference_id=subtask.id,
            is_read=False
        )
        db.add(problem_notif)
        db.commit()
        return {"message": "Issue reported to owner."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))