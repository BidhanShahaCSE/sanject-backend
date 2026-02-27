from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.db.database import get_db
from app.model.assignment_model import Assignment
from app.model.assignment_subtask_model import AssignmentSubTask
from app.model.user_model import User
from app.model.project_model import Project 
from app.model.project_member_model import ProjectMember 
from app.model.notification_model import Notification
from app.model.note_model import Note
from app.model.assignment_subtask_note_link_model import AssignmentSubtaskNoteLink

# Schemas
from app.schemas.assignment_schemas import AssignmentCreate, AssignmentOut, AssignmentUpdate
from app.schemas.assignment_subtask_schemas import (
    AssignmentSubTaskCreate, 
    AssignmentSubTaskOut, 
    AssignmentSubTaskUpdate
)

from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/assignments",
    tags=["Assignments & SubTasks"]
)

ALLOWED_TASK_TYPES = ["Assignment", "Lab Report", "Exam", "Home Work"]


class ShareProjectLinkRequest(BaseModel):
    drive_link: str
    recipient_email: EmailStr


class ReportProblemRequest(BaseModel):
    recipient_email: EmailStr
    problem_text: str

# ----------------------------------------------------------------
# 🚀 1. Main Assignment Section
# ----------------------------------------------------------------

# Creating Assignments
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

        # Notification to owner
        owner_notification = Notification(
            user_id=owner.id,
            title="Assignment Created",
            message=f"You successfully created {new_assignment.task_type}: '{new_assignment.org_name}'",
            type="assignment",
            reference_id=new_assignment.id,
            is_read=False
        )
        db.add(owner_notification)

        # Notification to Members
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

# View a list of all assignments
@router.get("/", response_model=List[AssignmentOut])
def get_all_assignments(db: Session = Depends(get_db)):
    return db.query(Assignment).all()

# View assignments with specific IDs
@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment_by_id(assignment_id: int, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.get("/{assignment_id}/subtasks", response_model=List[AssignmentSubTaskOut])
def get_subtasks_by_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    subtasks = (
        db.query(AssignmentSubTask)
        .filter(AssignmentSubTask.assignment_id == assignment_id)
        .order_by(AssignmentSubTask.created_at.desc())
        .all()
    )
    return subtasks


@router.post("/{assignment_id}/share-project")
def share_assignment_project_link(
    assignment_id: int,
    data: ShareProjectLinkRequest,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    link = data.drive_link.strip()
    if not link:
        raise HTTPException(status_code=400, detail="Drive link is required")

    sender = db.query(User).filter(User.email == current_user_email).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    receiver = db.query(User).filter(User.email == data.recipient_email).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Recipient email is not registered")

    try:
        db.add(
            Notification(
                user_id=receiver.id,
                title=f"Assignment link from {sender.email}",
                message=f"{sender.email} shared an assignment drive link: {link}",
                type="assignment_share",
                reference_id=assignment.id,
                is_read=False,
            )
        )
        db.commit()
        return {"message": "Project link sent successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send link: {str(e)}")


@router.post("/{assignment_id}/report-problem")
def report_assignment_problem(
    assignment_id: int,
    data: ReportProblemRequest,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    problem_text = data.problem_text.strip()
    if not problem_text:
        raise HTTPException(status_code=400, detail="Problem text is required")

    sender = db.query(User).filter(User.email == current_user_email).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    receiver = db.query(User).filter(User.email == data.recipient_email).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Recipient email is not registered")

    try:
        db.add(
            Notification(
                user_id=receiver.id,
                title=f"Problem report from {sender.email}",
                message=f"{sender.email} reported: {problem_text}",
                type="assignment_problem",
                reference_id=assignment.id,
                is_read=False,
            )
        )
        db.commit()
        return {"message": "Problem report sent successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send problem report: {str(e)}")

# Deleting assignments
@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    db_assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    try:
        db.delete(db_assignment)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

# ----------------------------------------------------------------
# 🚀 2. Sub-Task Section
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

@router.patch("/subtasks/{subtask_id}", response_model=AssignmentSubTaskOut)
def update_subtask(
    subtask_id: int,
    data: AssignmentSubTaskUpdate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    subtask_query = db.query(AssignmentSubTask).filter(
        AssignmentSubTask.id == subtask_id, 
        AssignmentSubTask.owner_email == current_user_email 
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

@router.delete("/subtasks/{subtask_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subtask(
    subtask_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    db_subtask = db.query(AssignmentSubTask).filter(
        AssignmentSubTask.id == subtask_id, 
        AssignmentSubTask.owner_email == current_user_email 
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
# 3. Submission & Reporting
# ----------------------------------------------------------------

@router.post("/subtasks/{subtask_id}/complete-submission")
def full_submission_notification(
    subtask_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    subtask = db.query(AssignmentSubTask).filter(AssignmentSubTask.id == subtask_id).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")

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
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")

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


@router.post("/subtasks/{subtask_id}/note")
def ensure_subtask_note(
    subtask_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    normalized_email = (current_user_email or "").strip().lower()
    subtask = db.query(AssignmentSubTask).filter(AssignmentSubTask.id == subtask_id).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")

    link = (
        db.query(AssignmentSubtaskNoteLink)
        .filter(
            AssignmentSubtaskNoteLink.subtask_id == subtask_id,
            func.lower(AssignmentSubtaskNoteLink.owner_email) == normalized_email,
        )
        .first()
    )

    if link:
        existing_note = (
            db.query(Note)
            .filter(
                Note.id == link.note_id,
                func.lower(Note.owner_email) == normalized_email,
            )
            .first()
        )
        if existing_note:
            return existing_note

    note = Note(
        name=f"Subtask Note: {subtask.name}",
        description=f"Linked to subtask '{subtask.name}'",
        owner_email=normalized_email,
    )

    try:
        db.add(note)
        db.flush()

        db.add(
            AssignmentSubtaskNoteLink(
                subtask_id=subtask_id,
                note_id=note.id,
                owner_email=normalized_email,
            )
        )
        db.commit()
        db.refresh(note)
        return note
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create subtask note: {str(e)}")


@router.get("/subtasks/{subtask_id}/note")
def get_subtask_note(
    subtask_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    normalized_email = (current_user_email or "").strip().lower()
    link = (
        db.query(AssignmentSubtaskNoteLink)
        .filter(
            AssignmentSubtaskNoteLink.subtask_id == subtask_id,
            func.lower(AssignmentSubtaskNoteLink.owner_email) == normalized_email,
        )
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="No note found for this subtask")

    note = (
        db.query(Note)
        .filter(Note.id == link.note_id, func.lower(Note.owner_email) == normalized_email)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Linked note not found")
    return note


@router.post("/subtasks/{subtask_id}/share-project")
def share_subtask_project_link(
    subtask_id: int,
    data: ShareProjectLinkRequest,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    link = data.drive_link.strip()
    if not link:
        raise HTTPException(status_code=400, detail="Drive link is required")

    subtask = db.query(AssignmentSubTask).filter(AssignmentSubTask.id == subtask_id).first()
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")

    sender = db.query(User).filter(User.email == current_user_email).first()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    receiver = db.query(User).filter(User.email == data.recipient_email).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Recipient email is not registered")

    try:
        db.add(
            Notification(
                user_id=receiver.id,
                title=f"Project link from {sender.email}",
                message=f"{sender.email} shared a drive link: {link}",
                type="project_share",
                reference_id=subtask.id,
                is_read=False,
            )
        )
        db.commit()
        return {"message": "Project link sent successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to send link: {str(e)}")