from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.model.note_model import Note 
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# 🛡️ টোকেন থেকে ইমেইল পাওয়ার ডিপেন্ডেন্সি ইম্পোর্ট করুন
from app.api.v1.endpoints.auth.auth_utils import get_current_user_email 

router = APIRouter(
    prefix="/notes",
    tags=["Notes"]
)

class NoteCreate(BaseModel):
    name: str
    description: Optional[str] = None
    # owner_email এখন আর ইনপুট হিসেবে দরকার নেই 🚀

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

# 🚀 ১. নতুন নোট তৈরি করা (টোকেন থেকে ইমেইল অটোমেটিক আসবে)
@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    note_data: NoteCreate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 টোকেন চেক
):
    new_note = Note(
        name=note_data.name,
        description=note_data.description,
        owner_email=current_user_email # সরাসরি টোকেনের ইমেইল ব্যবহার হচ্ছে
    )
    try:
        db.add(new_note)
        db.commit()
        db.refresh(new_note)
        return new_note
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 🚀 ২. নোটের কন্টেন্ট আপডেট করা (মালিকানা যাচাই অটোমেটিক)
@router.patch("/{note_id}/write", response_model=NoteResponse)
def write_note_content(
    note_id: int, 
    content_data: NoteUpdate, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 টোকেন চেক
):
    # শুধুমাত্র টোকেনের ইমেইলের সাথে মিললে তবেই আপডেট হবে
    db_note = db.query(Note).filter(Note.id == note_id, Note.owner_email == current_user_email).first()
    
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found or unauthorized")
    
    db_note.content = content_data.content 
    db.commit()
    db.refresh(db_note)
    return db_note

# 🚀 ৩. ইউজারের সব নোটের লিস্ট দেখা (অটোমেটিক ফিল্টার)
@router.get("/", response_model=List[NoteResponse])
def get_user_notes(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 টোকেন চেক
):
    # ইউজারকে এখন আর ইমেইল পাঠাতে হবে না, সে শুধু নিজের নোটগুলোই দেখবে
    return db.query(Note).filter(Note.owner_email == current_user_email).all()

# 🚀 ৪. নির্দিষ্ট নোট ডিলিট করা (মালিকানা যাচাই অটোমেটিক)
@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int, 
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email) # 🔒 টোকেন চেক
):
    # মালিকানা যাচাই করে নোটটি খুঁজে বের করা
    note = db.query(Note).filter(Note.id == note_id, Note.owner_email == current_user_email).first()

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