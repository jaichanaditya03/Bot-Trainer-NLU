"""
Project management routes
"""
from fastapi import APIRouter, HTTPException, status, Header
from typing import Annotated, Optional
from datetime import datetime
from models import ProjectCreate
from auth import decode_token
from database import projects_col

router = APIRouter()

AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]


@router.post("/projects", status_code=status.HTTP_201_CREATED)
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


@router.get("/projects")
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
