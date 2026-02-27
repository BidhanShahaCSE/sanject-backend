import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel # Schemas তৈরির জন্য
from app.db.database import get_db
from app.model.gemini_model import GeminiChat

router = APIRouter(prefix="/ai", tags=["Gemini AI Chat"])

# --- ১. পূর্ণাঙ্গ Schemas (Pydantic Models) ---

class ChatRequest(BaseModel):
    """ইউজার যখন নতুন প্রশ্ন পাঠাবে"""
    prompt: str

class EditRequest(BaseModel):
    """ইউজার যখন পুরনো চ্যাট এডিট করবে"""
    new_prompt: str

# --- ২. Gemini কনফিগারেশন ---

# আপনার স্ক্রিনশট থেকে পাওয়া API Key এখানে দিন
genai.configure(api_key="AIzaSyCKyr5FN81JvoNhIuRK7wErgpAWVYr-pDI") 
model = genai.GenerativeModel('gemini-1.5-flash')

# --- ৩. API Endpoints (CRUD) ---

# ক. নতুন চ্যাট করা এবং ডাটাবেসে সেভ করা
@router.post("/chat")
def create_chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        # Gemini থেকে উত্তর আনা
        response = model.generate_content(request.prompt)
        
        # ডাটাবেস মডেলে ডেটা রাখা
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

# খ. সব চ্যাট হিস্ট্রি দেখা
@router.get("/chats")
def get_all_chats(db: Session = Depends(get_db)):
    return db.query(GeminiChat).all()

# গ. আইডি দিয়ে নির্দিষ্ট চ্যাট দেখা
@router.get("/chat/{chat_id}")
def get_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(GeminiChat).filter(GeminiChat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

# ঘ. চ্যাট এডিট করা (আবার নতুন রেসপন্স তৈরি হবে)
@router.put("/chat/{chat_id}")
def edit_chat(chat_id: int, request: EditRequest, db: Session = Depends(get_db)):
    chat = db.query(GeminiChat).filter(GeminiChat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # নতুন এডিট করা প্রশ্নের ভিত্তিতে AI রেসপন্স
    response = model.generate_content(request.new_prompt)
    chat.prompt = request.new_prompt
    chat.ai_response = response.text
    
    db.commit()
    return chat

# ঙ. চ্যাট ডিলিট করা
@router.delete("/chat/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(GeminiChat).filter(GeminiChat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted successfully from database"}