from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.db.database import get_db
from app.model.note_model import Note 
from app.model.user_model import User
from app.model.assignment_subtask_note_link_model import AssignmentSubtaskNoteLink
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# 🛡️ Import email power dependencies from tokens
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/notes",
    tags=["Notes"]
)

class NoteCreate(BaseModel):
    name: str
    description: Optional[str] = None

class NoteUpdate(BaseModel):
    content: str 

class NoteResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    content: Optional[str]
    owner_email: str
    created_at: datetime

    class Config:
        from_attributes = True


# 🚀 1. Create a new note
@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    note_data: NoteCreate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    normalized_email = (current_user_email or "").strip().lower()
    owner = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if not owner:
        raise HTTPException(status_code=404, detail="User not found")

    new_note = Note(
        name=note_data.name,
        description=note_data.description,
        owner_email=normalized_email
    )
    try:
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        return new_note
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 🚀 2. Updating the content of the note
@router.patch("/{note_id}/write", response_model=NoteResponse)
def write_note_content(
    note_id: int, 
    content_data: NoteUpdate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    normalized_email = (current_user_email or "").strip().lower()
    db_note = db.query(Note).filter(
        Note.id == note_id, 
        func.lower(Note.owner_email) == normalized_email
    ).first()
    
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found or unauthorized")
    
    db_note.content = content_data.content 
    db.commit()
    db.refresh(db_note)
    return db_note

# Add this to your fastapi router file
@router.patch("/{note_id}/write", response_model=NoteResponse)
def update_note_content(
    note_id: int, 
    content_data: NoteUpdate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    normalized_email = (current_user_email or "").strip().lower()
    db_note = db.query(Note).filter(
        Note.id == note_id,
        func.lower(Note.owner_email) == normalized_email,
    ).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db_note.content = content_data.content 
    db.commit()
    db.refresh(db_note)
    return db_note
# 3. View a list of all user notes
@router.get("/", response_model=List[NoteResponse])
def get_user_notes(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    normalized_email = (current_user_email or "").strip().lower()
    linked_note_ids = [
        row[0]
        for row in db.query(AssignmentSubtaskNoteLink.note_id)
        .filter(func.lower(AssignmentSubtaskNoteLink.owner_email) == normalized_email)
        .all()
    ]

    query = db.query(Note).filter(func.lower(Note.owner_email) == normalized_email)
    if linked_note_ids:
        query = query.filter(~Note.id.in_(linked_note_ids))

    return query.all()


# 🚀 4. Delete specific notes
@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    normalized_email = (current_user_email or "").strip().lower()
    note = db.query(Note).filter(
        Note.id == note_id, 
        func.lower(Note.owner_email) == normalized_email
    ).first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Note not found or unauthorized"
        )

    try:
        db.delete(note)
        db.commit()
        return None 
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


# 5. View note details by note id (NEW API)
@router.get("/{note_id}", response_model=NoteResponse)
def get_note_details(
    note_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    normalized_email = (current_user_email or "").strip().lower()
    note = db.query(Note).filter(
        Note.id == note_id,
        func.lower(Note.owner_email) == normalized_email
    ).first()

    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or unauthorized"
        )

    return note