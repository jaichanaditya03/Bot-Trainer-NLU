from datetime import datetime
from typing import Annotated, List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel

from auth import decode_token
from database import active_learning_corrections_col, workspaces_col
from .nlu_routes import BatchPredictPayload, predict_batch  # type: ignore

router = APIRouter(prefix="/active-learning", tags=["Active Learning"])

AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]


class SuggestRequest(BaseModel):
    texts: List[str]
    actual_intents: Optional[List[str]] = None  # Ground truth labels for filtering
    model_id: Optional[str] = "spacy"
    threshold: Optional[float] = 0.5  # max confidence to keep (uncertain <= threshold)


class FeedbackItem(BaseModel):
    text: str
    predicted_intent: Optional[str] = None
    predicted_confidence: Optional[float] = None
    corrected_intent: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    remarks: Optional[str] = None
    model_id: Optional[str] = None
    model_name: Optional[str] = None


class SaveFeedbackRequest(BaseModel):
    items: List[FeedbackItem]


@router.post("/suggest", status_code=status.HTTP_200_OK)
def suggest_uncertain_samples(payload: SuggestRequest, authorization: AuthorizationHeader = None):
    """Return low-confidence predictions for active learning.

    Uses existing /predict/batch implementation and filters by confidence.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decode_token(token)

    if not payload.texts:
        raise HTTPException(status_code=400, detail="texts must be non-empty")

    try:
        batch_payload = BatchPredictPayload(
            texts=payload.texts,
            model_id=payload.model_id or "spacy",
            allowed_intents=None,
            strict=False,
        )
        raw = predict_batch(batch_payload, authorization=authorization)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {e}")

    preds = raw.get("predictions", []) if isinstance(raw, dict) else []
    thr = float(payload.threshold or 0.5)
    actual_intents = payload.actual_intents or []
    has_labels = len(actual_intents) == len(payload.texts)

    items = []
    for idx, p in enumerate(preds):
        if not isinstance(p, dict):
            continue
        text = str(p.get("text", ""))
        intent = str(p.get("intent", "unknown"))
        conf = float(p.get("confidence", 0.0) or 0.0)
        
        # Get actual intent if available
        actual = None
        if has_labels and idx < len(actual_intents):
            actual = str(actual_intents[idx]).strip().lower()
        
        predicted = intent.strip().lower()
        
        # Only include samples that are:
        # 1. Wrong prediction (predicted != actual), OR
        # 2. Low confidence (conf <= threshold) AND prediction doesn't match actual
        # This filters out correct predictions with low confidence
        
        if actual is not None:
            # We have ground truth - use it for smart filtering
            if predicted != actual:
                # Prediction is wrong - include regardless of confidence
                items.append({
                    "text": text,
                    "predicted_intent": intent,
                    "predicted_confidence": conf,
                    "is_wrong": True,
                })
            elif conf <= thr:
                # Prediction is correct but low confidence - include as "needs review"
                items.append({
                    "text": text,
                    "predicted_intent": intent,
                    "predicted_confidence": conf,
                    "is_wrong": False,
                })
        else:
            # No ground truth - fall back to confidence-only filtering
            if conf <= thr:
                items.append({
                    "text": text,
                    "predicted_intent": intent,
                    "predicted_confidence": conf,
                    "is_wrong": None,  # Unknown if wrong
                })

    # Sort by wrong predictions first, then by ascending confidence
    items.sort(key=lambda x: (not x.get("is_wrong", False), x.get("predicted_confidence", 0.0)))

    return {
        "model_id": payload.model_id or "spacy",
        "threshold": thr,
        "count": len(items),
        "items": items,
        "filtering_strategy": "smart" if has_labels else "confidence_only",
        "wrong_predictions": sum(1 for x in items if x.get("is_wrong") is True),
    }


@router.post("/corrections", status_code=status.HTTP_201_CREATED)
def save_corrections(payload: SaveFeedbackRequest, authorization: AuthorizationHeader = None):
    """Persist corrected training data from active learning into MongoDB."""
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
            "workspace_id": workspace_id,  # Store workspace context
            "text": item.text,
            "predicted_intent": (item.predicted_intent or "").strip().lower() or None,
            "predicted_confidence": float(item.predicted_confidence) if item.predicted_confidence is not None else None,
            "corrected_intent": (item.corrected_intent or "").strip().lower() or None,
            "entities": item.entities or [],
            "remarks": item.remarks or "",
            "model_id": (item.model_id or "").strip().lower() or None,
            "model_name": item.model_name or None,
            "created_at": now,
        }
        docs.append(doc)

    if docs:
        active_learning_corrections_col.insert_many(docs)

    return {"message": "Corrections saved", "count": len(docs)}


@router.get("/corrections", status_code=status.HTTP_200_OK)
def get_corrections(authorization: AuthorizationHeader = None):
    """Retrieve all active learning corrections saved by the current user for their active workspace."""
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
        # Return empty results if no workspace is selected
        return {
            "count": 0,
            "items": [],
            "message": "No active workspace selected"
        }
    
    # Query corrections for this user AND workspace, sorted by most recent first
    cursor = active_learning_corrections_col.find({
        "owner_email": email,
        "workspace_id": workspace_id
    }).sort("created_at", -1)
    items = []
    
    for doc in cursor:
        # Convert ObjectId to string
        doc["_id"] = str(doc.get("_id", ""))
        items.append(doc)
    
    return {
        "count": len(items),
        "items": items
    }
