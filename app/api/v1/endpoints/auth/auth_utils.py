from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader # 👈 Import it
from jose import jwt, JWTError

SECRET_KEY = "your_super_secret_key" 
ALGORITHM = "HS256"

# 🛡️ This will directly generate the token pasting box
# Putting 'Authorization' in the 'name' field means it will go as a header
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
        # If the token is in the format 'Bearer <token>' then the 'Bearer' part must be omitted
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise credentials_exception
        return email
        
    except JWTError:
        raise credentials_exception