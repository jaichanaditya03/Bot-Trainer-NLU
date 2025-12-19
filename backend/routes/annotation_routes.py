
from fastapi import APIRouter, HTTPException, status, Header
from typing import Annotated, Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from auth import decode_token
from database import annotations_col, dataset_sentences_col

router = APIRouter()

AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]


class AnnotationData(BaseModel):
    """Single annotation entry"""
    sentence: str
    intent: str
    entities: List[Dict[str, Any]]  # [{"text": "New York", "label": "location", "start": 20, "end": 28}]


class SaveAnnotationsRequest(BaseModel):
    """Request to save annotations"""
    dataset_checksum: str
    workspace_id: Optional[str] = None
    annotations: List[AnnotationData]


@router.post("/annotations/save", status_code=status.HTTP_201_CREATED)
def save_annotations(data: SaveAnnotationsRequest, authorization: AuthorizationHeader = None):
    """Save annotated data for a dataset"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    # Verify dataset exists in dataset_sentences collection
    dataset = dataset_sentences_col.find_one({"owner_email": decoded["email"]})
    if not dataset:
        raise HTTPException(status_code=404, detail="No dataset found")

    # Check if dataset checksum exists
    entries = dataset.get("entries", [])
    dataset_entry = next((e for e in entries if e.get("checksum") == data.dataset_checksum), None)
    if not dataset_entry:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Extract annotations with proper entity structure
    annotations_list = []
    for ann in data.annotations:
        annotation_dict = {
            "sentence": ann.sentence,
            "intent": ann.intent,
            "entities": ann.entities  # This will preserve the full entity structure
        }
        annotations_list.append(annotation_dict)

    # Save annotations
    annotation_doc = {
        "owner_email": decoded["email"],
        "workspace_id": data.workspace_id,
        "dataset_checksum": data.dataset_checksum,
        "dataset_filename": dataset_entry.get("filename"),
        "annotations": annotations_list,
        "annotation_count": len(annotations_list),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    existing = annotations_col.find_one({
        "owner_email": decoded["email"],
        "dataset_checksum": data.dataset_checksum
    })

    if existing:
        # Append new annotations to existing ones instead of replacing
        annotations_col.update_one(
            {"owner_email": decoded["email"], "dataset_checksum": data.dataset_checksum},
            {
                "$push": {"annotations": {"$each": annotations_list}},
                "$inc": {"annotation_count": len(annotations_list)},
                "$set": {"updated_at": annotation_doc["updated_at"]}
            }
        )
    else:
        annotations_col.insert_one(annotation_doc)

    return {"message": "Annotations saved successfully", "count": len(data.annotations)}


@router.get("/annotations/{dataset_checksum}")
def get_annotations(dataset_checksum: str, authorization: AuthorizationHeader = None):
    """Get annotations for a specific dataset"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    annotation_doc = annotations_col.find_one({
        "owner_email": decoded["email"],
        "dataset_checksum": dataset_checksum
    }, {"_id": 0})

    return annotation_doc or {"annotations": [], "annotation_count": 0}


@router.get("/annotations/export/{dataset_checksum}")
def export_annotations(dataset_checksum: str, authorization: AuthorizationHeader = None):
    """Export annotations in training format"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    annotation_doc = annotations_col.find_one({
        "owner_email": decoded["email"],
        "dataset_checksum": dataset_checksum
    })

    if not annotation_doc:
        raise HTTPException(status_code=404, detail="No annotations found")

    # Convert to training format (Rasa/spaCy compatible)
    training_data = []
    for ann in annotation_doc.get("annotations", []):
        training_data.append({
            "text": ann["sentence"],
            "intent": ann["intent"],
            "entities": ann["entities"]
        })

    return {
        "training_data": training_data,
        "count": len(training_data),
        "filename": annotation_doc.get("dataset_filename", "annotations")
    }
