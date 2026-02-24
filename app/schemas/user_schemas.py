from pydantic import BaseModel, EmailStr
from typing import Optional

# ১. লগইন রিকোয়েস্ট স্কিমা (আগের মতোই থাকবে)
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# ২. লগইন রেসপন্স স্কিমা (পরিবর্তন করতে হবে) 🚀
class LoginResponse(BaseModel):
    message: str
    access_token: str        # স্বল্পমেয়াদী টোকেন
    refresh_token: str       # দীর্ঘমেয়াদী টোকেন (নতুন যোগ করা হয়েছে)
    token_type: str = "bearer"
    user_id: int
    role: str

# ৩. টোকেন রিফ্রেশ করার জন্য নতুন স্কিমা 🚀
class TokenRefreshRequest(BaseModel):
    refresh_token: str