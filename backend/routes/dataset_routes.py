"""
Dataset management routes
"""
from fastapi import APIRouter, HTTPException, status, Header
from typing import Annotated, Optional
from datetime import datetime
import jwt
from models import DatasetPayload, DatasetSelection
from auth import decode_token
from database import datasets_col
from config import JWT_SECRET, JWT_ALGO

router = APIRouter()

AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]


@router.post("/datasets", status_code=status.HTTP_201_CREATED)
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


@router.get("/datasets")
def get_dataset(authorization: AuthorizationHeader = None):
    """Retrieve persisted dataset summary for a user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    dataset = datasets_col.find_one({"owner_email": decoded["email"]}, {"_id": 0})
    return dataset or {}


@router.post("/datasets/select")
def set_selected_dataset(data: DatasetSelection, authorization: AuthorizationHeader = None):
    """Select a specific dataset as active"""
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
