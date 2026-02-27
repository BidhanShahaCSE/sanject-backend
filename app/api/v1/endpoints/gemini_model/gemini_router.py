import os
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv
from app.db.database import get_db
from app.model.gemini_model import GeminiChat
import google.generativeai as genai
# .env ফাইল থেকে API Key লোড করার জন্য
load_dotenv()

router = APIRouter(prefix="/ai", tags=["Gemini AI Chat"])

# এনভায়রনমেন্ট থেকে সিক্রেট কি রিড করা
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise ValueError("GEMINI_API_KEY missing in .env file! Please add it.")

# Gemini কনফিগারেশন
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- ১. Schemas (ডেটা আদান-প্রদানের ফরম্যাট) ---

class ChatRequest(BaseModel):
    prompt: str

class EditRequest(BaseModel):
    new_prompt: str

# --- ২. API Endpoints (CRUD) ---

# ক. নতুন চ্যাট তৈরি করা (Create)
@router.post("/chat")
def create_chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # AI থেকে রেসপন্স জেনারেট করা
        response = model.generate_content(request.prompt)
        
        # ডাটাবেসে সেভ করা
        new_chat = GeminiChat(
            prompt=request.prompt,
            ai_response=response.text
        )
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        return new_chat
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")

# খ. সব চ্যাট লিস্ট দেখা (Read All)
@router.get("/chats")
def get_all_chats(db: Session = Depends(get_db)):
    return db.query(GeminiChat).all()

# গ. নির্দিষ্ট একটি চ্যাট দেখা (Read Specific)
@router.get("/chat/{chat_id}")
def get_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(GeminiChat).filter(GeminiChat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return chat

# ঘ. পুরনো চ্যাট এডিট করা (Update)
@router.put("/chat/{chat_id}")
def edit_chat(chat_id: int, request: EditRequest, db: Session = Depends(get_db)):
    chat = db.query(GeminiChat).filter(GeminiChat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found to edit")
    
    try:
        # নতুন প্রম্পট অনুযায়ী AI রেসপন্স আপডেট করা
        response = model.generate_content(request.new_prompt)
        chat.prompt = request.new_prompt
        chat.ai_response = response.text
        
        db.commit()
        db.refresh(chat)
        return chat
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Update Error: {str(e)}")

# ঙ. চ্যাট ডিলিট করা (Delete)
@router.delete("/chat/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(GeminiChat).filter(GeminiChat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found to delete")
    
    db.delete(chat)
    db.commit()
    return {"message": "Chat history deleted successfully", "id": chat_id}