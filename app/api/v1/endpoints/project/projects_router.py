from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.model.project_member_model import ProjectMember
from app.model.project_model import Project
from app.model.user_model import User 
from app.schemas.project_member_schemas import ProjectMembersUpdateList
from app.schemas.project_schemas import ProjectCreate, ProjectResponse, ProjectUpdate

# 🛡️ Token theke email pawar dependency
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

# 🚀 1. Creating new projects (member validation and notification to all including owner)
@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    user = db.query(User).filter(User.email == current_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for email in project_data.members_email:
        reg_user = db.query(User).filter(User.email == email).first()
        if not reg_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Member email '{email}' is not a registered user."
            )

    members_str = ",".join(project_data.members_email)

    new_project = Project(
        project_name=project_data.project_name,
        description=project_data.description,
        start_date=project_data.start_date,
        deadline=project_data.deadline,
        owner_id=user.id,
        owner_email=current_user_email,
        members_email=members_str
    )
    
    try:
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        # 1. Adding entries to the ProjectMember table
        for email in project_data.members_email:
            new_member_entry = ProjectMember(
                project_id=new_project.id,
                email=email,
                role="Pending", 
                description="Assign responsibility later", 
                start_date=new_project.start_date,
                deadline=new_project.deadline
            )
            db.add(new_member_entry)

        db.commit() 
        return new_project
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# 🚀 2. Updating Member Responsibilities (including Notification)
@router.patch("/{project_id}/update-members-details")
def update_members_details(
    project_id: int, 
    data: ProjectMembersUpdateList, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_email == current_user_email).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    for member_info in data.members:
        registered_user = db.query(User).filter(User.email == member_info.member_email).first()
        if not registered_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Email '{member_info.member_email}' is not registered."
            )

        db_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.email == member_info.member_email
        ).first()

        if db_member:
            db_member.role = member_info.role
            db_member.description = member_info.description
            db_member.start_date = member_info.start_date
            db_member.deadline = member_info.deadline
        else:
            new_member = ProjectMember(
                project_id=project_id,
                email=member_info.member_email,
                role=member_info.role,
                description=member_info.description,
                start_date=member_info.start_date,
                deadline=member_info.deadline
            )
            db.add(new_member)
        
        # 🔔 Member Responsibility Update Notification
        update_notif = Notification(
            user_id=registered_user.id,
            title="Project Role Updated",
            message=f"Your responsibility in '{project.project_name}' has been updated to: {member_info.role}",
            type="project",
            reference_id=project.id,
            is_read=False
        )
        db.add(update_notif)

    try:
        db.commit()
        return {"message": "Member details updated and notifications sent successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 3. View all projects
@router.get("/", response_model=List[ProjectResponse])
def get_all_projects(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    return db.query(Project).filter(Project.owner_email == current_user_email).all()


@router.get("/{project_id}/my-member-info")
def get_my_project_member_info(
    project_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.owner_email == current_user_email:
        return {
            "role": "Owner",
            "description": "",
            "is_owner": True,
        }

    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.email == current_user_email,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member info not found")

    return {
        "role": member.role or "Member",
        "description": member.description or "",
        "is_owner": False,
    }

# 🚀 4. Updating project information
@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int, 
    project_data: ProjectUpdate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    project_query = db.query(Project).filter(Project.id == project_id, Project.owner_email == current_user_email)
    db_project = project_query.first()

    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    update_data = project_data.model_dump(exclude_unset=True)
    if "members_email" in update_data and update_data["members_email"]:
        update_data["members_email"] = ",".join(update_data["members_email"])

    try:
        project_query.update(update_data, synchronize_session=False)
        db.commit()
        db.refresh(db_project)
        return db_project
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

# 5. Delete the project
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_email == current_user_email).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    try:
        db.delete(project)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Delete failed: {str(e)}")