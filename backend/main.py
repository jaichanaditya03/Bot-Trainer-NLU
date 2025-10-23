from fastapi import FastAPI, HTTPException, status
from fastapi.params import Header
from typing import Annotated, Optional, Any, Dict
import re
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from dotenv import load_dotenv
import bcrypt
import jwt
import os
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict

# ---------------- LOAD ENV VARIABLES ----------------
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "bot_trainer")
JWT_SECRET = os.getenv("JWT_SECRET", "mysecretkey123")
JWT_ALGO = "HS256"

# ---------------- INIT ----------------
app = FastAPI(title="Bot Trainer Backend")

# Allow Streamlit frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- DB CONNECTION ----------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_col = db["users"]
projects_col = db["projects"]
datasets_col = db["datasets"]

# ---------------- TOKEN HELPER ----------------
def create_token(email: str, username: Optional[str] = None):
    """Generate JWT token for a user"""
    payload = {
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=12)
    }
    if username:
        payload["username"] = username
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    return token

def decode_token(token: str):
    """Decode JWT token and verify"""
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return decoded
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------- API ROUTES ----------------
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def username_not_blank(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Username must be at least 2 characters.")
        return value

    @field_validator("password")
    @classmethod
    def password_strength(cls, value: str) -> str:
        if len(value) < 6 or not re.search(r"[^\w\s]", value):
            raise ValueError("Password must be at least 6 characters and include at least one special character.")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Project name cannot be empty.")
        return value

    @field_validator("description")
    @classmethod
    def description_trim(cls, value: Optional[str]) -> str:
        if value is None:
            return ""
        return value.strip()


class DatasetPayload(BaseModel):
    filename: str
    analysis: Dict[str, Any]
    evaluation: Dict[str, Any]
    checksum: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class DatasetSelection(BaseModel):
    checksum: str
    filename: Optional[str] = None



AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest):
    """Register a new user"""
    if users_col.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt())
    users_col.insert_one({
        "username": data.username,
        "email": data.email,
        "password": hashed.decode("utf-8"),
        "created_at": datetime.utcnow()
    })
    return {"message": "User registered successfully"}

@app.post("/login")
def login(data: LoginRequest):
    """User login with JWT token"""
    user = users_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(data.password.encode("utf-8"), user["password"].encode("utf-8")):
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

@app.post("/projects", status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, authorization: AuthorizationHeader = None):
    """Create a new project (requires JWT)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    project_doc = {
        "name": data.name,
        "description": data.description or "",
        "owner_email": decoded["email"],
        "created_at": datetime.utcnow()
    }
    projects_col.insert_one(project_doc)
    return {"message": "Project created successfully"}

@app.get("/projects")
def get_projects(authorization: AuthorizationHeader = None):
    """List user projects (requires JWT)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    projects = list(projects_col.find(
        {"owner_email": decoded["email"]},
        {"_id": 0}
    ))
    return projects


@app.post("/datasets", status_code=status.HTTP_201_CREATED)
def save_dataset(data: DatasetPayload, authorization: AuthorizationHeader = None):
    """Persist processed dataset summary for a user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    checksum = data.checksum or jwt.encode({"filename": data.filename, "timestamp": datetime.utcnow().timestamp()}, JWT_SECRET, algorithm=JWT_ALGO)
    entry = {
        "owner_email": decoded["email"],
        "filename": data.filename,
        "analysis": data.analysis,
        "evaluation": data.evaluation,
        "updated_at": datetime.utcnow(),
        "checksum": checksum,
    }

    existing = datasets_col.find_one({"owner_email": decoded["email"]})
    if existing:
        entries = existing.get("entries", [])
        deduped = []
        for item in entries:
            if item.get("checksum") == checksum:
                continue
            if data.filename and item.get("filename") == data.filename:
                continue
            deduped.append(item)

        deduped.insert(0, entry)
        deduped = deduped[:5]

        previous_selected = existing.get("selected") or {}
        selected_checksum = previous_selected.get("checksum")
        selected_entry = next((item for item in deduped if item.get("checksum") == selected_checksum), None)
        if not selected_entry:
            selected_entry = entry

        datasets_col.update_one(
            {"owner_email": decoded["email"]},
            {
                "$set": {
                    "owner_email": decoded["email"],
                    "entries": deduped,
                    "selected": selected_entry,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
    else:
        datasets_col.insert_one({
            "owner_email": decoded["email"],
            "entries": [entry],
            "selected": entry,
            "updated_at": datetime.utcnow(),
        })

    return {"message": "Dataset saved successfully", "checksum": checksum}


@app.get("/datasets")
def get_dataset(authorization: AuthorizationHeader = None):
    """Retrieve persisted dataset summary for a user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    dataset = datasets_col.find_one({"owner_email": decoded["email"]}, {"_id": 0})
    return dataset or {}


@app.post("/datasets/select")
def set_selected_dataset(data: DatasetSelection, authorization: AuthorizationHeader = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    dataset = datasets_col.find_one({"owner_email": decoded["email"]})
    if not dataset:
        raise HTTPException(status_code=404, detail="No datasets available")

    entries = dataset.get("entries", [])
    match = next((entry for entry in entries if entry.get("checksum") == data.checksum), None)
    if not match:
        raise HTTPException(status_code=404, detail="Dataset not found")

    datasets_col.update_one(
        {"owner_email": decoded["email"]},
        {"$set": {"selected": match, "updated_at": datetime.utcnow()}},
    )

    return {"message": "Dataset selected", "selected": match}
