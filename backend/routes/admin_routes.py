"""
Admin Panel Routes - User, Workspace, Dataset, and Model Management
"""
from fastapi import APIRouter, HTTPException, status, Header
from typing import Annotated, Optional, List
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId
import io
import json

from auth import decode_token, hash_password
from database import users_col, workspaces_col, datasets_col, dataset_sentences_col, feedback_col, annotations_col

router = APIRouter(prefix="/admin", tags=["Admin"])

AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]


def verify_admin(authorization: AuthorizationHeader):
    """Verify user is authenticated - in production, add admin role check"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)
    email = decoded.get("email")
    
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Check if user has admin role
    user = users_col.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return email


# ===== USER MANAGEMENT =====

@router.get("/users", status_code=status.HTTP_200_OK)
def list_users(authorization: AuthorizationHeader = None):
    """Get list of all registered users"""
    verify_admin(authorization)
    
    users = []
    for user in users_col.find({}, {"password": 0}):  # Exclude password
        user["_id"] = str(user.get("_id", ""))
        user["created_at"] = str(user.get("created_at", ""))
        users.append(user)
    
    return {"users": users, "count": len(users)}


@router.delete("/users/{email}", status_code=status.HTTP_200_OK)
def delete_user(email: str, authorization: AuthorizationHeader = None):
    """Remove a user and all their data"""
    verify_admin(authorization)
    
    user = users_col.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete user's workspaces
    workspaces_col.delete_many({"owner_email": email})
    
    # Delete user's datasets
    datasets_col.delete_many({"owner_email": email})
    
    # Delete user's feedback
    feedback_col.delete_many({"owner_email": email})
    
    # Delete user's annotations
    annotations_col.delete_many({"owner_email": email})
    
    # Delete user account
    users_col.delete_one({"email": email})
    
    return {"message": f"User {email} and all associated data deleted successfully"}


class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str


@router.post("/users/reset-password", status_code=status.HTTP_200_OK)
def reset_user_password(data: ResetPasswordRequest, authorization: AuthorizationHeader = None):
    """Reset a user's password (admin only)"""
    verify_admin(authorization)
    
    user = users_col.find_one({"email": data.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hashed = hash_password(data.new_password)
    users_col.update_one(
        {"email": data.email},
        {"$set": {"password": hashed, "password_reset_at": datetime.utcnow()}}
    )
    
    return {"message": f"Password reset successfully for {data.email}"}


# ===== WORKSPACE MANAGEMENT =====

@router.get("/workspaces", status_code=status.HTTP_200_OK)
def list_all_workspaces(authorization: AuthorizationHeader = None):
    """Get all workspaces across all users"""
    verify_admin(authorization)
    
    all_workspaces = []
    
    # Iterate through all workspace documents
    for ws_doc in workspaces_col.find({}):
        owner_email = ws_doc.get("owner_email", "Unknown")
        workspaces_array = ws_doc.get("workspaces", [])
        
        # Extract each individual workspace from the array
        for workspace in workspaces_array:
            workspace_entry = {
                "workspace_id": workspace.get("id"),
                "name": workspace.get("name", "Unnamed"),
                "description": workspace.get("description", ""),
                "owner_email": owner_email,
                "created_at": str(workspace.get("created_at", ""))
            }
            all_workspaces.append(workspace_entry)
    
    return {"workspaces": all_workspaces, "count": len(all_workspaces)}


@router.get("/workspaces/{workspace_id}", status_code=status.HTTP_200_OK)
def get_workspace_details(workspace_id: str, authorization: AuthorizationHeader = None):
    """Get detailed information about a specific workspace"""
    verify_admin(authorization)
    
    # Find the workspace document that contains this workspace_id
    ws_doc = workspaces_col.find_one({"workspaces.id": workspace_id})
    if not ws_doc:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Find the specific workspace in the array
    workspace = None
    for ws in ws_doc.get("workspaces", []):
        if ws.get("id") == workspace_id:
            workspace = ws
            break
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get associated datasets
    datasets = list(datasets_col.find({"workspace_id": workspace_id}))
    for ds in datasets:
        ds["_id"] = str(ds.get("_id", ""))
    
    # Get feedback count
    feedback_count = feedback_col.count_documents({"workspace_id": workspace_id})
    
    workspace_info = {
        "workspace_id": workspace.get("id"),
        "name": workspace.get("name"),
        "description": workspace.get("description", ""),
        "owner_email": ws_doc.get("owner_email"),
        "created_at": str(workspace.get("created_at", "")),
        "workspaces": ws_doc.get("workspaces", [])
    }
    
    return {
        "workspace": workspace_info,
        "datasets": datasets,
        "dataset_count": len(datasets),
        "feedback_count": feedback_count
    }


@router.delete("/workspaces/{workspace_id}", status_code=status.HTTP_200_OK)
def delete_workspace(workspace_id: str, authorization: AuthorizationHeader = None):
    """Delete a workspace and all associated data"""
    verify_admin(authorization)
    
    # Find the workspace document that contains this workspace_id
    ws_doc = workspaces_col.find_one({"workspaces.id": workspace_id})
    if not ws_doc:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Delete associated datasets from nested arrays
    datasets_col.update_many(
        {"datasets.workspace_id": workspace_id},
        {"$pull": {"datasets": {"workspace_id": workspace_id}}}
    )
    # Clean up documents with empty datasets arrays
    datasets_col.delete_many({"datasets": {"$size": 0}})
    
    # Delete associated feedback
    feedback_col.delete_many({"workspace_id": workspace_id})
    
    # Delete associated annotations
    annotations_col.delete_many({"workspace_id": workspace_id})
    
    # Remove the workspace from the array
    workspaces_col.update_one(
        {"_id": ws_doc["_id"]},
        {"$pull": {"workspaces": {"id": workspace_id}}}
    )
    
    # Clean up workspace document if no workspaces left
    workspaces_col.delete_many({"workspaces": {"$size": 0}})
    
    return {"message": f"Workspace {workspace_id} deleted successfully"}


@router.get("/workspaces/{workspace_id}/download", status_code=status.HTTP_200_OK)
def download_workspace_data(workspace_id: str, authorization: AuthorizationHeader = None):
    """Download workspace dataset, model info, and logs as JSON"""
    verify_admin(authorization)
    
    # Find the workspace document that contains this workspace_id
    ws_doc = workspaces_col.find_one({"workspaces.id": workspace_id})
    if not ws_doc:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Find the specific workspace in the array
    workspace = None
    for ws in ws_doc.get("workspaces", []):
        if ws.get("id") == workspace_id:
            workspace = ws
            break
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    # Get datasets
    datasets = list(datasets_col.find({"workspace_id": workspace_id}))
    for ds in datasets:
        ds["_id"] = str(ds.get("_id", ""))
    
    # Get feedback/corrections
    feedback = list(feedback_col.find({"workspace_id": workspace_id}))
    for fb in feedback:
        fb["_id"] = str(fb.get("_id", ""))
        fb["created_at"] = str(fb.get("created_at", ""))
    
    workspace_info = {
        "workspace_id": workspace.get("id"),
        "name": workspace.get("name"),
        "description": workspace.get("description", ""),
        "owner_email": ws_doc.get("owner_email"),
        "created_at": str(workspace.get("created_at", ""))
    }
    
    export_data = {
        "workspace": workspace_info,
        "datasets": datasets,
        "feedback": feedback,
        "exported_at": str(datetime.utcnow())
    }
    
    return export_data


# ===== DATASET MANAGEMENT =====

@router.get("/datasets", status_code=status.HTTP_200_OK)
def list_all_datasets(authorization: AuthorizationHeader = None):
    """Get all datasets with workspace info"""
    verify_admin(authorization)
    
    datasets = []
    
    # Iterate through all dataset documents
    for ds_doc in datasets_col.find({}):
        owner_email = ds_doc.get("owner_email", "Unknown")
        datasets_array = ds_doc.get("datasets", [])
        
        # Extract each individual dataset from the array
        for dataset in datasets_array:
            ws_id = dataset.get("workspace_id")
            
            # Get workspace name from nested structure
            workspace_name = "Unknown"
            if ws_id:
                ws_doc = workspaces_col.find_one({"workspaces.id": ws_id})
                if ws_doc:
                    for ws in ws_doc.get("workspaces", []):
                        if ws.get("id") == ws_id:
                            workspace_name = ws.get("name", "Unknown")
                            break
            
            # Count samples
            sample_data = dataset.get("data", [])
            sample_count = len(sample_data) if isinstance(sample_data, list) else 0
            
            dataset_entry = {
                "_id": str(ds_doc.get("_id", "")),
                "workspace_id": ws_id,
                "workspace_name": workspace_name,
                "filename": dataset.get("filename", "N/A"),
                "checksum": dataset.get("checksum", ""),
                "sample_count": sample_count,
                "owner_email": owner_email,
                "uploaded_at": str(dataset.get("uploaded_at", ""))
            }
            
            datasets.append(dataset_entry)
    
    return {"datasets": datasets, "count": len(datasets)}


@router.get("/datasets/{workspace_id}/view", status_code=status.HTTP_200_OK)
def view_workspace_dataset(workspace_id: str, authorization: AuthorizationHeader = None):
    """View dataset for a specific workspace"""
    verify_admin(authorization)
    
    # Find workspace in nested structure
    ws_doc = workspaces_col.find_one({"workspaces.id": workspace_id})
    if not ws_doc:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    workspace_name = "Unknown"
    for ws in ws_doc.get("workspaces", []):
        if ws.get("id") == workspace_id:
            workspace_name = ws.get("name", "Unknown")
            break
    
    # Get the latest dataset
    dataset = datasets_col.find_one(
        {"workspace_id": workspace_id},
        sort=[("uploaded_at", -1)]
    )
    
    if not dataset:
        raise HTTPException(status_code=404, detail="No dataset found for this workspace")
    
    dataset["_id"] = str(dataset.get("_id", ""))
    dataset["uploaded_at"] = str(dataset.get("uploaded_at", ""))
    
    # Get sample count
    sample_data = dataset.get("data", [])
    sample_count = len(sample_data) if isinstance(sample_data, list) else 0
    
    return {
        "workspace_name": workspace_name,
        "dataset": dataset,
        "sample_count": sample_count
    }


@router.delete("/datasets/{workspace_id}/{checksum}", status_code=status.HTTP_200_OK)
def delete_workspace_dataset(workspace_id: str, checksum: str, authorization: AuthorizationHeader = None):
    """Delete a specific dataset by workspace_id and checksum from BOTH collections"""
    verify_admin(authorization)
    
    # Delete from datasets collection (nested arrays) - remove specific dataset by checksum
    result1 = datasets_col.update_many(
        {"datasets.workspace_id": workspace_id, "datasets.checksum": checksum},
        {"$pull": {"datasets": {"workspace_id": workspace_id, "checksum": checksum}}}
    )
    
    # Clean up documents with empty datasets arrays
    datasets_col.delete_many({"datasets": {"$size": 0}})
    
    # Delete from dataset_sentences collection (nested arrays) - remove specific entry by checksum
    result2 = dataset_sentences_col.update_many(
        {"entries.workspace_id": workspace_id, "entries.checksum": checksum},
        {"$pull": {"entries": {"workspace_id": workspace_id, "checksum": checksum}}}
    )
    
    # Clean up documents with empty entries arrays
    dataset_sentences_col.delete_many({"entries": {"$size": 0}})
    
    total_modified = result1.modified_count + result2.modified_count
    
    if total_modified > 0:
        return {"message": f"Deleted dataset with checksum {checksum} from workspace {workspace_id}"}
    else:
        return {"message": "Dataset not found"}


@router.get("/datasets/{workspace_id}/download", status_code=status.HTTP_200_OK)
def download_workspace_dataset(workspace_id: str, authorization: AuthorizationHeader = None):
    """Download dataset for a workspace as JSON with all sentences"""
    verify_admin(authorization)
    
    # Get workspace name
    workspace_name = "Unknown"
    ws_doc = workspaces_col.find_one({"workspaces.id": workspace_id})
    if ws_doc:
        for ws in ws_doc.get("workspaces", []):
            if ws.get("id") == workspace_id:
                workspace_name = ws.get("name", "Unknown")
                break
    
    sentences = []
    filename = "dataset"
    
    # Search in datasets_col with nested structure
    for ds_doc in datasets_col.find({}):
        datasets_array = ds_doc.get("datasets", [])
        for dataset in datasets_array:
            if dataset.get("workspace_id") == workspace_id:
                # Extract from content structure
                content = dataset.get("content", {})
                filename = dataset.get("filename", "dataset")
                
                # Get all available data
                full_records = content.get("full_records", [])
                sample_records = content.get("sample_records", [])
                raw_sentences = content.get("sentences", [])
                
                # Priority 1: Use full_records if available (complete dataset)
                if full_records and len(full_records) > 0:
                    for record in full_records:
                        # Try different possible field names for sentence
                        sentence_text = (
                            record.get("sentence") or 
                            record.get("text") or 
                            record.get("utterance") or 
                            record.get("query") or 
                            record.get("message") or 
                            ""
                        )
                        
                        sentence_data = {
                            "sentence": sentence_text,
                            "intent": record.get("intent", ""),
                            "entities": record.get("entities", [])
                        }
                        if sentence_data["sentence"]:
                            sentences.append(sentence_data)
                
                # Priority 2: Use sample_records if no full_records
                elif sample_records and len(sample_records) > 0:
                    for record in sample_records:
                        sentence_text = (
                            record.get("sentence") or 
                            record.get("text") or 
                            record.get("utterance") or 
                            record.get("query") or 
                            record.get("message") or 
                            ""
                        )
                        
                        sentence_data = {
                            "sentence": sentence_text,
                            "intent": record.get("intent", ""),
                            "entities": record.get("entities", [])
                        }
                        if sentence_data["sentence"]:
                            sentences.append(sentence_data)
                
                # Priority 3: Just raw sentences without intents/entities
                elif raw_sentences and len(raw_sentences) > 0:
                    for sent in raw_sentences:
                        sentences.append({
                            "sentence": sent,
                            "intent": "",
                            "entities": []
                        })
                
                break
        if len(sentences) > 0:
            break
    
    if len(sentences) == 0:
        raise HTTPException(status_code=404, detail="No dataset found for this workspace")
    
    # Prepare download data
    download_data = {
        "workspace_id": workspace_id,
        "workspace_name": workspace_name,
        "filename": filename,
        "total_sentences": len(sentences),
        "data": sentences
    }
    
    return download_data


# ===== MODEL MANAGEMENT =====

@router.get("/models", status_code=status.HTTP_200_OK)
def list_all_models(authorization: AuthorizationHeader = None):
    """Get information about saved model comparisons"""
    verify_admin(authorization)
    
    from database import db
    model_comparisons_col = db["model_comparisons"]
    
    models = []
    
    # Get all model comparison documents
    for doc in model_comparisons_col.find({}).sort("saved_at", -1):
        workspace_id = doc.get("workspace_id")
        workspace_name = doc.get("workspace_name", "Unknown")
        saved_at = doc.get("saved_at", "")
        
        # Get workspace name from workspaces collection if not in doc
        if workspace_name == "Unknown" and workspace_id:
            ws_doc = workspaces_col.find_one({"workspaces.id": workspace_id})
            if ws_doc:
                for ws in ws_doc.get("workspaces", []):
                    if ws.get("id") == workspace_id:
                        workspace_name = ws.get("name", "Unknown")
                        break
        
        # Extract each model from the models array
        models_array = doc.get("models", [])
        for idx, model in enumerate(models_array):
            model_entry = {
                "_id": str(doc.get("_id", "")),
                "model_index": idx,  # Track position in array
                "workspace_id": workspace_id,
                "workspace_name": workspace_name,
                "model_name": model.get("model_name") or model.get("name", "Unknown"),
                "version": model.get("version", "N/A"),
                "accuracy": model.get("accuracy", 0),
                "f1_score": model.get("f1", 0),
                "precision": model.get("precision", 0),
                "recall": model.get("recall", 0),
                "train_samples": model.get("trainSamples", 0),
                "test_samples": model.get("testSamples", 0),
                "saved_at": saved_at
            }
            models.append(model_entry)
    
    return {"models": models, "count": len(models)}


@router.delete("/models/{comparison_id}/{model_index}", status_code=status.HTTP_200_OK)
def delete_model_comparison(comparison_id: str, model_index: int, authorization: AuthorizationHeader = None):
    """Delete a specific model from a saved comparison document"""
    verify_admin(authorization)
    
    from database import db
    from bson import ObjectId
    model_comparisons_col = db["model_comparisons"]
    
    try:
        # First, get the document to check how many models it has
        doc = model_comparisons_col.find_one({"_id": ObjectId(comparison_id)})
        
        if not doc:
            raise HTTPException(status_code=404, detail="Model comparison not found")
        
        models_array = doc.get("models", [])
        
        # If this is the only model, delete the entire document
        if len(models_array) <= 1:
            model_comparisons_col.delete_one({"_id": ObjectId(comparison_id)})
            return {"message": "Last model deleted, comparison document removed"}
        
        # Otherwise, remove just this specific model from the array
        models_array.pop(model_index)
        
        # Update the document with the modified models array
        model_comparisons_col.update_one(
            {"_id": ObjectId(comparison_id)},
            {"$set": {"models": models_array}}
        )
        
        return {"message": "Model deleted successfully"}
        
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid comparison ID or model index: {str(e)}")


# ===== ACTIVITY LOGS =====

@router.get("/logs/uploads", status_code=status.HTTP_200_OK)
def get_upload_logs(authorization: AuthorizationHeader = None, limit: int = 50):
    """Get recent dataset upload activity"""
    verify_admin(authorization)
    
    uploads = []
    for ds in datasets_col.find({}, sort=[("uploaded_at", -1)], limit=limit):
        # Get workspace name from nested structure
        ws_id = ds.get("workspace_id")
        ws_doc = workspaces_col.find_one({"workspaces.id": ws_id})
        workspace_name = "Unknown"
        if ws_doc:
            for ws in ws_doc.get("workspaces", []):
                if ws.get("id") == ws_id:
                    workspace_name = ws.get("name", "Unknown")
                    break
        
        uploads.append({
            "workspace_id": ws_id,
            "workspace_name": workspace_name,
            "owner_email": ds.get("owner_email"),
            "filename": ds.get("filename"),
            "uploaded_at": str(ds.get("uploaded_at", "")),
            "sample_count": len(ds.get("data", []))
        })
    
    return {"uploads": uploads, "count": len(uploads)}


@router.get("/logs/corrections", status_code=status.HTTP_200_OK)
def get_correction_logs(authorization: AuthorizationHeader = None, limit: int = 50):
    """Get recent correction/feedback activity"""
    verify_admin(authorization)
    
    corrections = []
    for fb in feedback_col.find({}, sort=[("created_at", -1)], limit=limit):
        # Get workspace name from nested structure
        ws_id = fb.get("workspace_id")
        ws_doc = workspaces_col.find_one({"workspaces.id": ws_id})
        workspace_name = "Unknown"
        if ws_doc:
            for ws in ws_doc.get("workspaces", []):
                if ws.get("id") == ws_id:
                    workspace_name = ws.get("name", "Unknown")
                    break
        
        corrections.append({
            "workspace_id": ws_id,
            "workspace_name": workspace_name,
            "owner_email": fb.get("owner_email"),
            "model_name": fb.get("model_name"),
            "text": fb.get("text", "")[:50] + "..." if len(fb.get("text", "")) > 50 else fb.get("text", ""),
            "predicted": fb.get("predicted_intent"),
            "corrected": fb.get("corrected_intent"),
            "created_at": str(fb.get("created_at", ""))
        })
    
    return {"corrections": corrections, "count": len(corrections)}


@router.get("/logs/active-learning", status_code=status.HTTP_200_OK)
def get_active_learning_logs(authorization: AuthorizationHeader = None, limit: int = 50):
    """Get recent active learning correction activity"""
    verify_admin(authorization)
    
    from database import active_learning_corrections_col
    
    corrections = []
    for alc in active_learning_corrections_col.find({}, sort=[("created_at", -1)], limit=limit):
        # Get workspace name from nested structure
        ws_id = alc.get("workspace_id")
        ws_doc = workspaces_col.find_one({"workspaces.id": ws_id})
        workspace_name = "Unknown"
        if ws_doc:
            for ws in ws_doc.get("workspaces", []):
                if ws.get("id") == ws_id:
                    workspace_name = ws.get("name", "Unknown")
                    break
        
        corrections.append({
            "workspace_id": ws_id,
            "workspace_name": workspace_name,
            "owner_email": alc.get("owner_email"),
            "text": alc.get("text", "")[:50] + "..." if len(alc.get("text", "")) > 50 else alc.get("text", ""),
            "predicted": alc.get("predicted_intent"),
            "corrected": alc.get("corrected_intent"),
            "created_at": str(alc.get("created_at", ""))
        })
    
    return {"corrections": corrections, "count": len(corrections)}


@router.get("/logs/training", status_code=status.HTTP_200_OK)
def get_training_logs(authorization: AuthorizationHeader = None, limit: int = 50):
    """Get recent model training/retraining activity"""
    verify_admin(authorization)
    
    from database import db
    model_comparisons_col = db["model_comparisons"]
    
    trainings = []
    for mc in model_comparisons_col.find({}, sort=[("saved_at", -1)], limit=limit):
        workspace_id = mc.get("workspace_id")
        workspace_name = mc.get("workspace_name", "Unknown")
        saved_at = mc.get("saved_at", "")
        
        # Get workspace name if not in document
        if workspace_name == "Unknown" and workspace_id:
            ws_doc = workspaces_col.find_one({"workspaces.id": workspace_id})
            if ws_doc:
                for ws in ws_doc.get("workspaces", []):
                    if ws.get("id") == workspace_id:
                        workspace_name = ws.get("name", "Unknown")
                        break
        
        models_array = mc.get("models", [])
        for model in models_array:
            trainings.append({
                "workspace_id": workspace_id,
                "workspace_name": workspace_name,
                "model_name": model.get("model_name") or model.get("name", "Unknown"),
                "version": model.get("version", "N/A"),
                "accuracy": model.get("accuracy", 0),
                "f1_score": model.get("f1", 0),
                "saved_at": saved_at
            })
    
    return {"trainings": trainings, "count": len(trainings)}


# ===== ANNOTATIONS =====

@router.get("/annotations", status_code=status.HTTP_200_OK)
def get_all_annotations(authorization: AuthorizationHeader = None, limit: int = 100):
    """Get all annotation data from annotations collection"""
    verify_admin(authorization)
    
    result = []
    for ann in annotations_col.find({}, sort=[("created_at", -1)], limit=limit):
        owner_email = ann.get("owner_email")
        dataset_filename = ann.get("dataset_filename", "Unknown")
        
        # Get workspace name from nested structure
        ws_id = ann.get("workspace_id")
        ws_doc = workspaces_col.find_one({"workspaces.id": ws_id})
        workspace_name = "Unknown"
        if ws_doc:
            for ws in ws_doc.get("workspaces", []):
                if ws.get("id") == ws_id:
                    workspace_name = ws.get("name", "Unknown")
                    break
        
        # Extract individual annotations from the nested array
        annotations_list = ann.get("annotations", [])
        for annotation in annotations_list:
            result.append({
                "owner_email": owner_email,
                "workspace_name": workspace_name,
                "dataset_filename": dataset_filename,
                "sentence": annotation.get("sentence", ""),
                "intent": annotation.get("intent", ""),
                "entities": annotation.get("entities", [])
            })
    
    return {"annotations": result, "count": len(result)}


# ===== STATISTICS =====

@router.get("/stats", status_code=status.HTTP_200_OK)
def get_admin_statistics(authorization: AuthorizationHeader = None):
    """Get overall system statistics"""
    verify_admin(authorization)
    
    # Count total workspaces from nested array
    total_workspaces = 0
    for ws_doc in workspaces_col.find({}):
        total_workspaces += len(ws_doc.get("workspaces", []))
    
    # Count total datasets from nested array (not just documents)
    total_datasets = 0
    for ds_doc in datasets_col.find({}):
        total_datasets += len(ds_doc.get("datasets", []))
    
    # Calculate average datasets per workspace
    avg_datasets = round(total_datasets / total_workspaces, 2) if total_workspaces > 0 else 0
    
    # Count total individual annotations (not just documents)
    total_annotations = 0
    for ann_doc in annotations_col.find({}):
        # Sum up the annotation_count from each document
        total_annotations += ann_doc.get("annotation_count", 0)
    
    stats = {
        "total_users": users_col.count_documents({}),
        "total_workspaces": total_workspaces,
        "total_datasets": total_datasets,
        "total_corrections": feedback_col.count_documents({}),
        "total_annotations": total_annotations,
        "avg_datasets_per_workspace": avg_datasets
    }
    
    return stats
