from pydantic import BaseModel, EmailStr
from typing import Optional

# 1. Login Request Schema (remains as before)
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# 2. Login Response Schema (to be changed) 🚀
class LoginResponse(BaseModel):
    message: str
    access_token: str        # Short term token
    refresh_token: str       # Long Term Token (newly added)
    token_type: str = "bearer"
    user_id: int
    role: str

# 3. New schema for refreshing tokens 🚀
class TokenRefreshRequest(BaseModel):
    refresh_token: str