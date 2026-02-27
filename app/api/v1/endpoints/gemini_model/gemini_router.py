import os
import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv
from app.db.database import get_db
from app.model.gemini_model import GeminiChat

# .env ফাইল থেকে API Key লোড করার জন্য
load_dotenv()

router = APIRouter(prefix="/ai", tags=["Gemini AI Chat"])

# এনভায়রনমেন্ট থেকে সিক্রেট কি রিড করা
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise ValueError("GEMINI_API_KEY missing in .env file! Please add it.")

# Gemini কনফিগারেশন
genai.configure(api_key=GEMINI_KEY)


def _extract_model_name(model_obj) -> str:
    name = getattr(model_obj, "name", "") or ""
    return name.replace("models/", "")


def _resolve_initial_model_name() -> str:
    preferred = (os.getenv("GEMINI_MODEL") or "").strip()
    return preferred or "gemini-1.5-flash"


_model_name = _resolve_initial_model_name()
model = genai.GenerativeModel(_model_name)


def _generate_ai_response(prompt: str) -> str:
    global model, _model_name
    target_model = _resolve_initial_model_name()
    try:
        if _model_name != target_model:
            model = genai.GenerativeModel(target_model)
            _model_name = target_model

        response = model.generate_content(prompt)
        return getattr(response, "text", "") or ""
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=(
                f"AI model unavailable for '{target_model}'. "
                f"Set GEMINI_MODEL in environment if needed. Error: {error}"
            ),
        )

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
        ai_response = _generate_ai_response(request.prompt)
        
        # ডাটাবেসে সেভ করা
        new_chat = GeminiChat(
            prompt=request.prompt,
            ai_response=ai_response
        )
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        return new_chat
    except HTTPException:
        raise
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
        ai_response = _generate_ai_response(request.new_prompt)
        chat.prompt = request.new_prompt
        chat.ai_response = ai_response
        
        db.commit()
        db.refresh(chat)
        return chat
    except HTTPException:
        raise
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