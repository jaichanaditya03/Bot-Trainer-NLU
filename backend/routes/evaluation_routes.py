from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)
import numpy as np
import math
from datetime import datetime

# Import the batch predictor and payload
from .nlu_routes import predict_batch, BatchPredictPayload  # type: ignore

# Database
from database import db
model_comparisons_col = db["model_comparisons"]

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


# ---------- request/response models ----------
class EvalRequest(BaseModel):
    texts: List[str]
    true_intents: List[str]
    model_id: Optional[str] = "spacy"
    train_pct: Optional[int] = 80
    seed: Optional[int] = 42
    allowed_intents: Optional[List[str]] = None
    strict_mode: Optional[bool] = True


# ---------- helpers ----------
def safe_round(x: float) -> float:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return 0.0
    return float(x)


def metrics_summary(y_true: List[str], y_pred: List[str]) -> Dict[str, float]:
    if not y_true:
        return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}

    try:
        acc = float(accuracy_score(y_true, y_pred))
    except Exception:
        acc = 0.0

    try:
        prec, rec, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="macro", zero_division=0
        )
    except Exception:
        prec, rec, f1 = 0.0, 0.0, 0.0

    return {
        "accuracy": safe_round(acc),
        "precision": safe_round(prec),
        "recall": safe_round(rec),
        "f1": safe_round(f1),
    }


def per_intent_report(y_true: List[str], y_pred: List[str]) -> List[Dict[str, Any]]:
    labels = sorted(list(set(y_true) | set(y_pred)))
    if not labels:
        return []

    try:
        prec, rec, f1, support = precision_recall_fscore_support(
            y_true, y_pred, labels=labels, zero_division=0
        )
    except Exception:
        return [
            {"intent": l, "precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0}
            for l in labels
        ]

    rows = []
    for i, label in enumerate(labels):
        rows.append(
            {
                "intent": label,
                "precision": safe_round(float(prec[i])),
                "recall": safe_round(float(rec[i])),
                "f1": safe_round(float(f1[i])),
                "support": int(support[i]),
            }
        )
    return rows


def build_confusion(y_true: List[str], y_pred: List[str], labels: Optional[List[str]] = None):
    labels_used = sorted(list(set(y_true) | set(y_pred))) if labels is None else labels
    if not labels_used:
        return {"labels": [], "matrix": []}
    try:
        cm = confusion_matrix(y_true, y_pred, labels=labels_used)
        cm_list = cm.tolist()
    except Exception:
        cm_list = [[0 for _ in labels_used] for _ in labels_used]
    return {"labels": labels_used, "matrix": cm_list}


# ---------- main evaluation endpoint ----------
@router.post("/run", summary="Run evaluation")
def run_evaluation(req: EvalRequest, authorization: Optional[str] = Header(None)):
    if not req.texts or not req.true_intents or len(req.texts) != len(req.true_intents):
        raise HTTPException(status_code=400, detail="texts and true_intents must be same-length non-empty lists")

    n = len(req.texts)
    if n < 1:
        raise HTTPException(status_code=400, detail="no samples provided")

    indices = np.arange(n)
    train_frac = float(max(0, min(100, req.train_pct))) / 100.0

    try:
        stratify = np.array(req.true_intents) if len(set(req.true_intents)) > 1 else None
        train_idx, test_idx = train_test_split(
            indices,
            train_size=train_frac,
            random_state=req.seed or 42,
            stratify=stratify
        )
    except Exception:
        split_at = int(n * train_frac)
        train_idx = indices[:split_at]
        test_idx = indices[split_at:]

    if len(test_idx) == 0:
        if len(train_idx) > 0:
            test_idx = np.array([train_idx[-1]])
            train_idx = train_idx[:-1]
        else:
            test_idx = np.array([0])
            train_idx = np.array([])

    X_test = [req.texts[int(i)] for i in test_idx]
    y_test = [req.true_intents[int(i)] for i in test_idx]

    X_train = [req.texts[int(i)] for i in train_idx]
    y_train = [req.true_intents[int(i)] for i in train_idx]

    payload = BatchPredictPayload(
        texts=X_test,
        model_id=req.model_id or "spacy",
        allowed_intents=req.allowed_intents or [],
        strict=req.strict_mode,
    )

    try:
        response = predict_batch(payload, authorization=authorization)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {e}")

    preds = []
    if isinstance(response, dict):
        preds = response.get("predictions", [])
    elif isinstance(response, list):
        preds = response

    predicted_intents = []
    predicted_confidences = []

    for p in preds:
        try:
            intent = p.get("intent") if isinstance(p, dict) else str(p)
            conf = float(p.get("confidence", 0.0)) if isinstance(p, dict) else 0.0
        except Exception:
            intent = ""
            conf = 0.0

        predicted_intents.append(str(intent).strip().lower())
        predicted_confidences.append(max(0.0, min(1.0, float(conf))))

    true_intents = [str(t).strip().lower() for t in y_test]

    metrics = metrics_summary(true_intents, predicted_intents)
    per_intent = per_intent_report(true_intents, predicted_intents)

    labels_set = set(true_intents) | set(predicted_intents)
    if req.allowed_intents:
        labels_set |= set([str(x).lower() for x in req.allowed_intents])
    labels = sorted(labels_set)
    confusion = build_confusion(true_intents, predicted_intents, labels=labels)

    details = []
    for txt, t_lab, p_lab, conf in zip(X_test, true_intents, predicted_intents, predicted_confidences):
        details.append({
            "text": txt,
            "true_intent": t_lab,
            "predicted_intent": p_lab,
            "confidence": safe_round(float(conf)),
            "match": (t_lab == p_lab),
        })

    return {
        "model": req.model_id,
        "metrics": metrics,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "intent_details": details,
        "per_intent": per_intent,
        "confusion": confusion,
        "y_true": true_intents,
        "y_pred": predicted_intents,
        "X_test": X_test,
    }


# ---------- NEW ENDPOINT: save model comparison data ----------
class ModelComparisonSaveRequest(BaseModel):
    workspace_id: str
    workspace_name: Optional[str] = None
    models: List[Dict[str, Any]]


@router.post("/model-comparison/save")
def save_model_comparison(payload: ModelComparisonSaveRequest, authorization: Optional[str] = Header(None)):
    """
    Save model comparison table to MongoDB.
    Used when user clicks "Save to Database" on frontend.
    """

    doc = {
        "workspace_id": payload.workspace_id,
        "workspace_name": payload.workspace_name or "Unknown Workspace",
        "models": payload.models,
        "saved_at": datetime.utcnow().isoformat()
    }

    model_comparisons_col.insert_one(doc)

    return {"message": "Model comparison saved", "status": "ok"}
