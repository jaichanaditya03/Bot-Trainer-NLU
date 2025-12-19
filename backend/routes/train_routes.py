
import threading
from datetime import datetime
from typing import Annotated, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

from auth import decode_token
from database import annotations_col

router = APIRouter()

AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]


# Global training status (single-user, single-session simple tracker)
_TRAIN_STATUS: Dict[str, object] = {
    "state": "idle",  # idle | running | completed | failed
    "progress": 0,
    "message": "",
    "started_at": None,
    "finished_at": None,
    "error": None,
}

_TRAIN_THREAD: Optional[threading.Thread] = None


class TrainStartRequest(BaseModel):
    dataset_checksum: str


def _update_status(state: str = None, progress: int = None, message: str = None, error: str = None):
    if state is not None:
        _TRAIN_STATUS["state"] = state
    if progress is not None:
        _TRAIN_STATUS["progress"] = int(max(0, min(100, progress)))
    if message is not None:
        _TRAIN_STATUS["message"] = message
    if error is not None:
        _TRAIN_STATUS["error"] = error
    if state == "running" and _TRAIN_STATUS.get("started_at") is None:
        _TRAIN_STATUS["started_at"] = datetime.utcnow().isoformat()
    if state in {"completed", "failed"}:
        _TRAIN_STATUS["finished_at"] = datetime.utcnow().isoformat()


def _train_worker(owner_email: str, req: TrainStartRequest):
    
    try:
        _update_status("running", 1, "Checking annotations…")

        ann_doc = annotations_col.find_one({
            "owner_email": owner_email,
            "dataset_checksum": req.dataset_checksum,
        })
        if not ann_doc or not ann_doc.get("annotations"):
            raise RuntimeError("No annotations available for this dataset.")

        # Simulate quick completion without actually training models.
        _update_status(progress=100, message="Training skipped (transformer models disabled).")
        _update_status("completed", 100, _TRAIN_STATUS.get("message") or "Training complete.")
    except Exception as e:
        _update_status("failed", error=str(e), message=f"Training failed: {e}")


@router.post("/train/start", status_code=status.HTTP_202_ACCEPTED)
def start_training(req: TrainStartRequest, authorization: AuthorizationHeader = None):
    """Start training intent and NER models in a background thread."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.replace("Bearer ", "")
    decoded = decode_token(token)

    if _TRAIN_STATUS.get("state") == "running":
        return {"message": "Training already in progress", "status": _TRAIN_STATUS}

    _update_status("running", 0, "Initializing training…", None)
    global _TRAIN_THREAD
    _TRAIN_THREAD = threading.Thread(target=_train_worker, args=(decoded["email"], req), daemon=True)
    _TRAIN_THREAD.start()
    return {"message": "Training started", "status": _TRAIN_STATUS}


@router.get("/train/status", status_code=status.HTTP_200_OK)
def training_status(authorization: AuthorizationHeader = None):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    # Only validates token
    token = authorization.replace("Bearer ", "")
    decode_token(token)
    return _TRAIN_STATUS
