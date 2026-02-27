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
    candidates = [
        preferred,
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
        "gemini-pro",
    ]

    available = set()
    try:
        for listed_model in genai.list_models():
            methods = getattr(listed_model, "supported_generation_methods", []) or []
            if "generateContent" in methods:
                available.add(_extract_model_name(listed_model))
    except Exception:
        # list_models() fail করলে নিচের fallback list দিয়ে try করা হবে
        pass

    for name in candidates:
        if not name:
            continue
        if not available or name in available:
            return name

    return "gemini-pro"


_model_name = _resolve_initial_model_name()
model = genai.GenerativeModel(_model_name)


def _generate_ai_response(prompt: str) -> str:
    global model, _model_name

    retry_candidates = [
        _model_name,
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro-latest",
        "gemini-pro",
    ]

    tried = set()
    last_error = None

    for candidate in retry_candidates:
        if not candidate or candidate in tried:
            continue
        tried.add(candidate)

        try:
            active_model = genai.GenerativeModel(candidate)
            response = active_model.generate_content(prompt)
            model = active_model
            _model_name = candidate
            return getattr(response, "text", "") or ""
        except Exception as error:
            last_error = error

    raise HTTPException(
        status_code=502,
        detail=f"AI model unavailable. Tried: {', '.join(tried)}. Last error: {last_error}",
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