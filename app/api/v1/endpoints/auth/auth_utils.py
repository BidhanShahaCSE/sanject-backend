from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader # 👈 এটি ইম্পোর্ট করুন
from jose import jwt, JWTError

SECRET_KEY = "your_super_secret_key" 
ALGORITHM = "HS256"

# 🛡️ এটি সরাসরি টোকেন পেস্ট করার বক্স তৈরি করবে
# 'name' ফিল্ডে 'Authorization' দেওয়ার মানে হলো এটি হেডার হিসেবে যাবে
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

def get_current_user_email(token: str = Depends(api_key_header)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception

    try:
        # টোকেন যদি 'Bearer <token>' ফরম্যাটে থাকে তবে 'Bearer ' অংশটুকু বাদ দিতে হবে
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
        return email
        
    except JWTError:
        raise credentials_exception