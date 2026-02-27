import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.model.gemini_model import GeminiChat
from p_models import ChatRequest, EditRequest # আপনার pydantic মডেল ফোল্ডার অনুযায়ী

router = APIRouter(prefix="/ai", tags=["Gemini AI Chat"])

# আপনার API Key কনফিগার করুন
genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')

# ১. চ্যাট করা এবং সেভ করা
@router.post("/chat")
def create_chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        response = model.generate_content(request.prompt)
        new_chat = GeminiChat(
            prompt=request.prompt,
            ai_response=response.text
        )
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        return new_chat
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ২. সব চ্যাট দেখা
@router.get("/chats")
def get_all_chats(db: Session = Depends(get_db)):
    return db.query(GeminiChat).all()

# ৩. নির্দিষ্ট চ্যাট দেখা
@router.get("/chat/{chat_id}")
def get_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(GeminiChat).filter(GeminiChat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

# ৪. চ্যাট এডিট করা (আবার AI রেসপন্স জেনারেট হবে)
@router.put("/chat/{chat_id}")
def edit_chat(chat_id: int, request: EditRequest, db: Session = Depends(get_db)):
    chat = db.query(GeminiChat).filter(GeminiChat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    response = model.generate_content(request.new_prompt)
    chat.prompt = request.new_prompt
    chat.ai_response = response.text
    db.commit()
    return chat

# ৫. চ্যাট ডিলিট করা
@router.delete("/chat/{chat_id}")
def delete_chat(chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(GeminiChat).filter(GeminiChat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    db.delete(chat)
    db.commit()
    return {"message": "Chat deleted successfully"}