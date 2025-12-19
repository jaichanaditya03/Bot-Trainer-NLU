"""
Dataset management routes
"""
from fastapi import APIRouter, HTTPException, status, Header, UploadFile, File
from typing import Annotated, Optional
from datetime import datetime
import jwt
import os
import shutil
from pathlib import Path
from models import DatasetPayload, DatasetSelection
from auth import decode_token
from database import dataset_sentences_col, datasets_col
from config import JWT_SECRET, JWT_ALGO

router = APIRouter()

AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]

# Create uploaded_files directory if it doesn't exist
UPLOADED_FILES_DIR = Path(__file__).parent.parent.parent / "uploaded_files"
UPLOADED_FILES_DIR.mkdir(exist_ok=True)


@router.post("/datasets", status_code=status.HTTP_201_CREATED)
def save_dataset(data: DatasetPayload, authorization: AuthorizationHeader = None):
    """Persist complete dataset with intents, entities, and sentences"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    # Extract ALL sentences and (if provided) full records from the analysis data
    sentences = []
    full_records = []
    if data.analysis and "full_sentences" in data.analysis:
        sentences = data.analysis["full_sentences"]
    elif data.analysis and "sample" in data.analysis:
        sample_data = data.analysis["sample"]
        if isinstance(sample_data, list) and len(sample_data) > 0:
            first_record = sample_data[0]
            text_fields = [k for k in first_record.keys() if any(keyword in k.lower() for keyword in ["text", "utterance", "sentence", "query", "message"])]
            
            if text_fields:
                text_field = text_fields[0]
                sentences = [str(record.get(text_field, "")).strip() for record in sample_data if record.get(text_field)]
                sentences = [s for s in sentences if s]
    # Optional full records (complete rows) for better reload fidelity
    if data.analysis and isinstance(data.analysis, dict) and data.analysis.get("full_records"):
        try:
            if isinstance(data.analysis["full_records"], list):
                full_records = data.analysis["full_records"]
        except Exception:
            full_records = []

    checksum = data.checksum or jwt.encode({"filename": data.filename, "timestamp": datetime.utcnow().timestamp()}, JWT_SECRET, algorithm=JWT_ALGO)
    
    # Extract intents and entities from analysis
    intents = data.analysis.get("intents", []) if data.analysis else []
    entities = data.analysis.get("entities", []) if data.analysis else []
    intent_columns = data.analysis.get("intent_columns", []) if data.analysis else []
    entity_columns = data.analysis.get("entity_columns", []) if data.analysis else []
    stats = data.analysis.get("stats", {}) if data.analysis else {}
    sample_data = data.analysis.get("sample", []) if data.analysis else []
    
    # Create complete dataset entry with actual content
    # Determine active workspace (optional scoping)
    from database import workspaces_col
    workspace_id = None
    try:
        root_ws = workspaces_col.find_one({"owner_email": decoded["email"]}) or {}
        workspace_id = root_ws.get("selected_workspace_id")
    except Exception:
        workspace_id = None

    if workspace_id is None:
        raise HTTPException(status_code=409, detail="No active workspace selected. Please click on a workspace in the 'Workspaces' section to select it before uploading datasets.")

    dataset_entry = {
        "owner_email": decoded["email"],
        "filename": data.filename,
        "checksum": checksum,
        "uploaded_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "workspace_id": workspace_id,
        
        # Dataset statistics
        "stats": {
            "total_rows": stats.get("rows", len(sentences)),
            "total_columns": stats.get("columns", 0),
            "sentence_count": len(sentences),
            "intent_count": len(intents),
            "entity_count": len(entities),
        },
        
        # Dataset structure
        "structure": {
            "intent_columns": intent_columns,
            "entity_columns": entity_columns,
        },
        
        # Complete dataset content
        "content": {
            "sentences": sentences,  # All text sentences
            "intents": intents,  # List of unique intents
            "entities": entities,  # List of unique entities
            "sample_records": sample_data[:50],  # First 50 records with all columns
            "full_records": full_records or sample_data,  # Store ALL records for download
        },
        
        # Distribution data (for analytics)
        "distributions": {
            "intent_distribution": data.analysis.get("intent_distribution", []) if data.analysis else [],
            "entity_distribution": data.analysis.get("entity_distribution", []) if data.analysis else [],
        }
    }
    
    # Save to dataset_sentences collection (only sentences for annotation)
    sentences_entry = {
        "owner_email": decoded["email"],
        "filename": data.filename,
        "sentences": sentences,
        "sentence_count": len(sentences),
        "updated_at": datetime.utcnow(),
        "checksum": checksum,
        "workspace_id": workspace_id,
    }
    
    existing_sentences = dataset_sentences_col.find_one({"owner_email": decoded["email"]})
    if existing_sentences:
        entries = existing_sentences.get("entries", [])
        deduped = []
        for item in entries:
            if item.get("checksum") == checksum:
                continue
            if data.filename and item.get("filename") == data.filename:
                continue
            deduped.append(item)

        deduped.insert(0, sentences_entry)
        deduped = deduped[:5]

        # Preserve selection per workspace if possible
        selected_by_workspace = existing_sentences.get("selected_by_workspace", {})
        previous_selected = None
        if workspace_id:
            previous_selected = selected_by_workspace.get(workspace_id)
        if not previous_selected:
            previous_selected = existing_sentences.get("selected") or {}

        selected_checksum = (previous_selected or {}).get("checksum")
        selected_entry = next((item for item in deduped if item.get("checksum") == selected_checksum and (not workspace_id or item.get("workspace_id") == workspace_id)), None)
        if not selected_entry:
            selected_entry = sentences_entry

        update_doc = {
            "owner_email": decoded["email"],
            "entries": deduped,
            "selected": selected_entry,
            "updated_at": datetime.utcnow(),
        }
        if workspace_id:
            update_doc[f"selected_by_workspace.{workspace_id}"] = selected_entry

        dataset_sentences_col.update_one(
            {"owner_email": decoded["email"]},
            {"$set": update_doc},
        )
    else:
        base_doc = {
            "owner_email": decoded["email"],
            "entries": [sentences_entry],
            "selected": sentences_entry,
            "updated_at": datetime.utcnow(),
        }
        if workspace_id:
            base_doc["selected_by_workspace"] = {workspace_id: sentences_entry}
        dataset_sentences_col.insert_one(base_doc)
    
    # Save to datasets collection (complete dataset with intents, entities, etc.)
    existing_datasets = datasets_col.find_one({"owner_email": decoded["email"]})
    if existing_datasets:
        dataset_entries = existing_datasets.get("datasets", [])
        dataset_deduped = []
        for item in dataset_entries:
            if item.get("checksum") == checksum:
                continue
            if data.filename and item.get("filename") == data.filename:
                continue
            dataset_deduped.append(item)

        dataset_deduped.insert(0, dataset_entry)
        dataset_deduped = dataset_deduped[:5]  # Keep last 5 datasets

        datasets_col.update_one(
            {"owner_email": decoded["email"]},
            {"$set": {"datasets": dataset_deduped, "updated_at": datetime.utcnow()}}
        )
    else:
        datasets_col.insert_one({
            "owner_email": decoded["email"],
            "datasets": [dataset_entry],
            "updated_at": datetime.utcnow(),
        })

    return {"message": "Dataset saved successfully", "checksum": checksum}


@router.get("/datasets")
def get_dataset(authorization: AuthorizationHeader = None):
    """Retrieve persisted dataset summary for a user (workspace scoped if selected)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    workspace_id = None
    from database import workspaces_col
    try:
        root_ws = workspaces_col.find_one({"owner_email": decoded["email"]}) or {}
        workspace_id = root_ws.get("selected_workspace_id")
    except Exception:
        workspace_id = None

    dataset = dataset_sentences_col.find_one({"owner_email": decoded["email"]}, {"_id": 0})
    if dataset and workspace_id:
        # Filter entries by workspace_id
        filtered_entries = [e for e in dataset.get("entries", []) if e.get("workspace_id") == workspace_id]
        if filtered_entries:
            # Adjust selected if not in filtered list
            selected = dataset.get("selected")
            if not selected or selected.get("workspace_id") != workspace_id:
                selected = filtered_entries[0]
            dataset = {
                "owner_email": decoded["email"],
                "entries": filtered_entries,
                "selected": selected,
                "updated_at": dataset.get("updated_at"),
            }
    return dataset or {}


@router.post("/datasets/select")
def set_selected_dataset(data: DatasetSelection, authorization: AuthorizationHeader = None):
    """Select a specific dataset as active"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    dataset = dataset_sentences_col.find_one({"owner_email": decoded["email"]})
    if not dataset:
        raise HTTPException(status_code=404, detail="No datasets available")

    # Workspace-aware selection
    workspace_id = None
    from database import workspaces_col
    try:
        root_ws = workspaces_col.find_one({"owner_email": decoded["email"]}) or {}
        workspace_id = root_ws.get("selected_workspace_id")
    except Exception:
        workspace_id = None

    entries = dataset.get("entries", [])
    if workspace_id:
        entries = [e for e in entries if e.get("workspace_id") == workspace_id]
    match = next((entry for entry in entries if entry.get("checksum") == data.checksum), None)
    if not match:
        raise HTTPException(status_code=404, detail="Dataset not found")

    update_doc = {"selected": match, "updated_at": datetime.utcnow()}
    if workspace_id:
        update_doc[f"selected_by_workspace.{workspace_id}"] = match

    dataset_sentences_col.update_one(
        {"owner_email": decoded["email"]},
        {"$set": update_doc},
    )

    return {"message": "Dataset selected", "selected": match}


@router.get("/datasets/complete/{checksum}")
def get_complete_dataset(checksum: str, authorization: AuthorizationHeader = None):
    """Get complete dataset with intents, entities, and all content"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    dataset = datasets_col.find_one({"owner_email": decoded["email"]})
    if not dataset:
        raise HTTPException(status_code=404, detail="No datasets found")

    datasets_list = dataset.get("datasets", [])
    # Optional workspace scoping for complete view
    from database import workspaces_col
    try:
        root_ws = workspaces_col.find_one({"owner_email": decoded["email"]}) or {}
        workspace_id = root_ws.get("selected_workspace_id")
        if workspace_id:
            datasets_list = [d for d in datasets_list if d.get("workspace_id") == workspace_id]
    except Exception:
        pass
    target_dataset = next((ds for ds in datasets_list if ds.get("checksum") == checksum), None)
    
    if not target_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Remove _id from response
    target_dataset.pop("_id", None)
    
    return target_dataset
