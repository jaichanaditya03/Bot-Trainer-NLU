"""
Workspace management routes
"""
from fastapi import APIRouter, HTTPException, status, Header
from typing import Annotated, Optional
from datetime import datetime
from models import WorkspaceCreate, WorkspaceSelect
from auth import decode_token
from database import workspaces_col

router = APIRouter()

AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]


def _ensure_root(owner_email: str):
    root = workspaces_col.find_one({"owner_email": owner_email})
    if not root:
        root = {
            "owner_email": owner_email,
            "workspaces": [],
            "selected_workspace_id": None,
            "created_at": datetime.utcnow(),
        }
        workspaces_col.insert_one(root)
    return root


@router.get("/workspaces")
def get_workspaces(authorization: AuthorizationHeader = None):
    """List user workspaces and current selection (requires JWT)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    root = _ensure_root(decoded["email"])
    return {
        "workspaces": root.get("workspaces", []),
        "selected_workspace_id": root.get("selected_workspace_id"),
    }


@router.post("/workspaces/create", status_code=status.HTTP_201_CREATED)
def create_workspace(data: WorkspaceCreate, authorization: AuthorizationHeader = None):
    """Create a new workspace (requires JWT)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    root = _ensure_root(decoded["email"])
    # prevent duplicate names
    if any(w.get("name") == data.name for w in root.get("workspaces", [])):
        raise HTTPException(status_code=409, detail="Workspace with that name already exists")

    from uuid import uuid4
    wid = uuid4().hex[:12]
    ws_doc = {
        "id": wid,
        "name": data.name,
        "description": data.description or "",
        "created_at": datetime.utcnow(),
    }
    workspaces_col.update_one(
        {"owner_email": decoded["email"]},
        {"$push": {"workspaces": ws_doc}},
        upsert=True,
    )
    # Auto-select if none selected
    if not root.get("selected_workspace_id"):
        workspaces_col.update_one(
            {"owner_email": decoded["email"]},
            {"$set": {"selected_workspace_id": wid}},
        )

    return {"message": "Workspace created successfully", "workspace": ws_doc}


@router.post("/workspaces/select")
def select_workspace(data: WorkspaceSelect, authorization: AuthorizationHeader = None):
    """Select active workspace (requires JWT)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    root = _ensure_root(decoded["email"])
    if not any(w.get("id") == data.workspace_id for w in root.get("workspaces", [])):
        raise HTTPException(status_code=404, detail="Workspace not found")

    workspaces_col.update_one(
        {"owner_email": decoded["email"]},
        {"$set": {"selected_workspace_id": data.workspace_id}},
    )
    return {"message": "Workspace selected", "workspace_id": data.workspace_id}
