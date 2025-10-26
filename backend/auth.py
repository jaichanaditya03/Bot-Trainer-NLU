"""
Authentication utilities - JWT and password hashing
"""
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from typing import Optional
from config import JWT_SECRET, JWT_ALGO, JWT_EXPIRY_HOURS


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_token(email: str, username: Optional[str] = None) -> str:
    """Generate JWT token for a user"""
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    if username:
        payload["username"] = username
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token


def decode_token(token: str) -> dict:
    """Decode JWT token and verify"""
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
