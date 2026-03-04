import os
from datetime import datetime, timedelta, UTC
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

oauth2_scheme_driver = OAuth2PasswordBearer(tokenUrl="/auth/driver/login")
oauth2_scheme_rider = OAuth2PasswordBearer(tokenUrl="/auth/rider/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(
    user_id: int,
    role: str,
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
) -> str:
    """Create JWT token"""
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
async def get_current_driver(
    token: str = Depends(oauth2_scheme_driver)
) -> dict:
    return decode_token(token)

async def get_current_rider(
    token: str = Depends(oauth2_scheme_rider)
) -> dict:
    return decode_token(token)


async def require_rider(
    current_user: dict = Depends(get_current_rider)
) -> dict:
    if current_user.get("role") != "rider":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Riders only"
        )
    return current_user


async def require_driver(
    current_user: dict = Depends(get_current_driver)
) -> dict:
    if current_user.get("role") != "driver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Drivers only"
        )
    return current_user

async def get_current_user(
    token: str = Depends(oauth2_scheme_rider)
) -> dict:
    return decode_token(token)