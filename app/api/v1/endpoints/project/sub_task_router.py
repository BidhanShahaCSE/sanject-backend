from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import os

from app.db.database import get_db
from app.model.project_model import Project
from app.model.project_member_model import ProjectMember
from app.model.subtask_model import SubTask # Your new model
from app.model.user_model import User 
from app.model.notification_model import Notification 

# 🛡️ Token theke email pawar dependency
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/subtasks",
    tags=["Project SubTasks"]
)

# 🚀 1. Uploading sub-tasks (only members can)
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_subtask(
    project_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    # Member Checking (Can't upload if not a member)
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id, 
        ProjectMember.email == current_user_email
    ).first()
    
    if not member:
        raise HTTPException(status_code=403, detail="Only assigned members can upload subtasks.")

    # File saving logic (change according to your path)
    upload_dir = "uploads/subtasks"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_path = f"{upload_dir}/{datetime.utcnow().timestamp()}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    new_subtask = SubTask(
        task_id=project_id,
        title=title,
        description=description,
        file_path=file_path
    )

    try:
        db.add(new_subtask)
        db.commit()
        db.refresh(new_subtask)

        # 2. Notification: will only go to members of that project
        project = db.query(Project).filter(Project.id == project_id).first()
        all_members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
        
        for m in all_members:
            if m.email != current_user_email: # Do not send to yourself
                target_user = db.query(User).filter(User.email == m.email).first()
                if target_user:
                    db.add(Notification(
                        user_id=target_user.id,
                        title="SubTask Uploaded",
                        message=f"New subtask '{title}' uploaded in project '{project.project_name}'",
                        type="subtask",
                        reference_id=new_subtask.id,
                        is_read=False
                    ))
        
        db.commit()
        return {"message": "Subtask uploaded and members notified.", "subtask_id": new_subtask.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 3. Total Project Submission (Owner and all members will get notification)
@router.post("/{project_id}/final-submit")
def final_project_submit(
    project_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Extract Owner ID and Members ID
    owner = db.query(User).filter(User.id == project.owner_id).first()
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()

    try:
        # 🔔 Sending notifications to him
        db.add(Notification(
            user_id=owner.id,
            title="Project Fully Submitted",
            message=f"The project '{project.project_name}' has been fully submitted by {current_user_email}",
            type="project_final",
            reference_id=project_id,
            is_read=False
        ))

        # 🔔 Sending notifications to all members
        for m in members:
            m_user = db.query(User).filter(User.email == m.email).first()
            if m_user:
                db.add(Notification(
                    user_id=m_user.id,
                    title="Submission Success",
                    message=f"Total submission complete for '{project.project_name}'",
                    type="project_final",
                    reference_id=project_id,
                    is_read=False
                ))
        
        db.commit()
        return {"message": "Final submission complete. Owner and all members notified."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 🚀 4. Sub-project viewing endpoint for managers and members
@router.get("/{project_id}/view-all", response_model=List[dict]) # Here you can replace the dictionary with your schema
def get_subtasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    # Check whether the user is the owner, manager or member of the project
    is_owner = db.query(Project).filter(Project.id == project_id, Project.owner_email == current_user_email).first()
    is_member = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.email == current_user_email).first()

    if not is_owner and not is_member:
        raise HTTPException(status_code=403, detail="Unauthorized to view subtasks of this project.")

    subtasks = db.query(SubTask).filter(SubTask.task_id == project_id).all()
    return subtasks