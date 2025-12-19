from datetime import datetime
from typing import Annotated, List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel

from auth import decode_token
from database import feedback_col, workspaces_col

router = APIRouter(prefix="/feedback", tags=["Feedback"])

AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]


class FeedbackItem(BaseModel):
    text: str  # User query
    predicted_intent: Optional[str] = None
    correct_intent: Optional[str] = None  # Editable
    entities: Optional[List[Dict[str, Any]]] = None  # Editable
    remarks: Optional[str] = None  # Feedback remarks


class SaveFeedbackRequest(BaseModel):
    items: List[FeedbackItem]


@router.post("/save", status_code=status.HTTP_201_CREATED)
def save_feedback(payload: SaveFeedbackRequest, authorization: AuthorizationHeader = None):
    """Save user feedback on model predictions."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)
    
    email = decoded.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token: missing email")

    if not payload.items:
        raise HTTPException(status_code=400, detail="items must be non-empty")
    
    # Get the user's current workspace_id
    user_workspace = workspaces_col.find_one({"owner_email": email})
    workspace_id = None
    if user_workspace:
        workspace_id = user_workspace.get("selected_workspace_id")
    
    if not workspace_id:
        raise HTTPException(
            status_code=400, 
            detail="No active workspace selected. Please select a workspace first."
        )

    docs = []
    now = datetime.utcnow()
    for item in payload.items:
        doc = {
            "owner_email": email,
            "workspace_id": workspace_id,
            "text": item.text,
            "predicted_intent": (item.predicted_intent or "").strip().lower() or None,
            "correct_intent": (item.correct_intent or "").strip().lower() or None,
            "entities": item.entities or [],
            "remarks": item.remarks or "",
            "created_at": now,
        }
        docs.append(doc)

    if docs:
        feedback_col.insert_many(docs)

    return {"message": "Feedback saved", "count": len(docs)}


@router.get("/list", status_code=status.HTTP_200_OK)
def get_feedback(authorization: AuthorizationHeader = None):
    """Retrieve all feedback items for the current user's active workspace."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)
    
    email = decoded.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token: missing email")
    
    # Get the user's current workspace_id
    user_workspace = workspaces_col.find_one({"owner_email": email})
    workspace_id = None
    if user_workspace:
        workspace_id = user_workspace.get("selected_workspace_id")
    
    if not workspace_id:
        return {
            "count": 0,
            "items": [],
            "message": "No active workspace selected"
        }
    
    # Query feedback for this user AND workspace, sorted by most recent first
    cursor = feedback_col.find({
        "owner_email": email,
        "workspace_id": workspace_id
    }).sort("created_at", -1)
    items = []
    
    for doc in cursor:
        doc["_id"] = str(doc.get("_id", ""))
        items.append(doc)
    
    return {
        "count": len(items),
        "items": items
    }
