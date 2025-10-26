"""
Authentication routes - register and login
"""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from models import RegisterRequest, LoginRequest
from auth import hash_password, verify_password, create_token
from database import users_col

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):
    """Register a new user"""
    if users_col.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(data.password)
    users_col.insert_one({
        "username": data.username,
        "email": data.email,
        "password": hashed,
        "created_at": datetime.utcnow()
    })
    return {"message": "User registered successfully"}


@router.post("/login")
def login(data: LoginRequest):
    """User login with JWT token"""
    user = users_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    username = user.get("username")
    token = create_token(data.email, username=username)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 12 * 60 * 60,
        "username": username,
        "message": "Login successful"
    }
