"""
Utility functions for dataset processing and analysis
"""
import json
import re
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import streamlit as st

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore
except ImportError:
    get_script_run_ctx = None  # type: ignore


def get_sidebar_toggle_state() -> bool:
    """Check if sidebar is toggled"""
    if get_script_run_ctx is None:
        return False
    try:
        ctx = get_script_run_ctx()
    except Exception:
        return False
    if not ctx or not hasattr(ctx, "session_state"):
        return False
    state = ctx.session_state
    try:
        return bool(state["_sidebar_toggled"])
    except KeyError:
        return False
    except Exception:
        try:
            return bool(getattr(state, "get", lambda *_, **__: False)("_sidebar_toggled", False))
        except Exception:
            return False


def _normalize_value(value, split_tokens=False):
    """Normalize values for intent/entity extraction"""
    if isinstance(value, pd.Series):
        return _normalize_value(value.dropna().tolist(), split_tokens=split_tokens)
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        tokens = []
        for item in value:
            tokens.extend(_normalize_value(item, split_tokens=split_tokens))
        return tokens
    if isinstance(value, dict):
        tokens = [*value.keys()]
        if split_tokens:
            for v in value.values():
                tokens.extend(_normalize_value(v, split_tokens=split_tokens))
        return [str(token).strip() for token in tokens if str(token).strip()]

    text = str(value).strip()
    if not text:
        return []
    if split_tokens:
        parts = [segment.strip() for segment in re.split(r"[,;/|]", text) if segment.strip()]
        if parts:
            return parts
    return [text]


def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze dataset for intents and entities"""
    stats = {"rows": int(df.shape[0]), "columns": int(df.shape[1])}
    lower_cols = {col: col.lower() for col in df.columns}

    intent_columns = [col for col, low in lower_cols.items() if "intent" in low]
    if not intent_columns:
        for alias in ("label", "category", "tag"):
            intent_columns.extend([col for col, low in lower_cols.items() if alias in low])
    intent_columns = list(dict.fromkeys(intent_columns))

    entity_columns = [col for col, low in lower_cols.items() if "entity" in low]
    if not entity_columns:
        for alias in ("slot", "parameter", "value"):
            entity_columns.extend([col for col, low in lower_cols.items() if alias in low])
    entity_columns = list(dict.fromkeys(entity_columns))

    intents = set()
    for col in intent_columns:
        intents.update(_normalize_value(df[col], split_tokens=False))

    entities = set()
    for col in entity_columns:
        entities.update(_normalize_value(df[col], split_tokens=True))

    intent_distribution = pd.DataFrame()
    if intent_columns:
        counts = df[intent_columns[0]].dropna().astype(str).str.strip()
        counts = counts[counts != ""]
        if not counts.empty:
            intent_distribution = counts.value_counts().reset_index(name="Count").rename(columns={"index": "Intent"})
            intent_distribution = intent_distribution.rename(columns=str.title)

    entity_distribution = pd.DataFrame()
    if entity_columns:
        entity_counter = Counter()
        for col in entity_columns:
            for item in df[col].dropna():
                entity_counter.update(_normalize_value(item, split_tokens=True))
        if entity_counter:
            entity_distribution = pd.DataFrame(entity_counter.most_common(25), columns=["Entity", "Count"])

    return {
        "stats": stats,
        "sample": df.head(50),
        "intent_columns": intent_columns,
        "entity_columns": entity_columns,
        "intents": sorted(intents),
        "entities": sorted(entities),
        "intent_distribution": intent_distribution,
        "entity_distribution": entity_distribution,
    }


def simulate_evaluation(df: pd.DataFrame, analysis: dict) -> Dict[str, Any]:
    """Simulate NLU evaluation metrics"""
    intents = analysis.get("intents", [])
    entities = analysis.get("entities", [])
    rows = analysis.get("stats", {}).get("rows", len(df)) or 1
    rng = np.random.default_rng(rows + len(intents) * 17 + len(entities) * 29)

    intent_acc = float(np.clip(0.78 + len(intents) * 0.005 + rng.normal(0.06, 0.02), 0.6, 0.99))
    entity_acc = float(np.clip(0.74 + len(entities) * 0.004 + rng.normal(0.05, 0.02), 0.55, 0.97))
    confusion_rate = float(np.clip(1 - ((intent_acc + entity_acc) / 2) + rng.normal(0.04, 0.015), 0.02, 0.25))

    metrics_df = pd.DataFrame([
        {"Metric": "Intent Accuracy", "Value": round(intent_acc * 100, 2)},
        {"Metric": "Entity Accuracy", "Value": round(entity_acc * 100, 2)},
        {"Metric": "Confusion Rate", "Value": round(confusion_rate * 100, 2)},
    ])

    intent_breakdown = pd.DataFrame()
    if intents:
        intent_scores = np.clip(rng.normal(intent_acc * 100, 5, size=len(intents)), 58, 99)
        intent_breakdown = pd.DataFrame({"Intent": intents, "Accuracy": np.round(intent_scores, 2)}).sort_values("Accuracy", ascending=False)

    entity_breakdown = pd.DataFrame()
    if entities:
        entity_scores = np.clip(rng.normal(entity_acc * 100, 6, size=len(entities)), 52, 98)
        entity_breakdown = pd.DataFrame({"Entity": entities, "Extraction Accuracy": np.round(entity_scores, 2)}).sort_values("Extraction Accuracy", ascending=False)

    confusion_df = pd.DataFrame({
        "Outcome": ["Correct", "Confused"],
        "Value": [round((1 - confusion_rate) * 100, 2), round(confusion_rate * 100, 2)],
    })

    return {
        "metrics_df": metrics_df,
        "intent_breakdown": intent_breakdown,
        "entity_breakdown": entity_breakdown,
        "confusion_df": confusion_df,
        "download_csv": metrics_df.to_csv(index=False).encode("utf-8"),
    }


def to_serializable(data: Any) -> Any:
    """Convert data to JSON serializable format"""
    try:
        return json.loads(json.dumps(data, default=str))
    except TypeError:
        return data


def serialize_analysis_for_api(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize analysis results for API"""
    sample_df: pd.DataFrame = analysis.get("sample", pd.DataFrame())
    intent_distribution: pd.DataFrame = analysis.get("intent_distribution", pd.DataFrame())
    entity_distribution: pd.DataFrame = analysis.get("entity_distribution", pd.DataFrame())

    return {
        "stats": analysis.get("stats", {}),
        "sample": to_serializable(sample_df.to_dict(orient="records")),
        "intent_columns": analysis.get("intent_columns", []),
        "entity_columns": analysis.get("entity_columns", []),
        "intents": analysis.get("intents", []),
        "entities": analysis.get("entities", []),
        "intent_distribution": to_serializable(intent_distribution.to_dict(orient="records")) if not intent_distribution.empty else [],
        "entity_distribution": to_serializable(entity_distribution.to_dict(orient="records")) if not entity_distribution.empty else [],
    }


def serialize_evaluation_for_api(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize evaluation results for API"""
    metrics_df: pd.DataFrame = evaluation.get("metrics_df", pd.DataFrame())
    intent_breakdown: pd.DataFrame = evaluation.get("intent_breakdown", pd.DataFrame())
    entity_breakdown: pd.DataFrame = evaluation.get("entity_breakdown", pd.DataFrame())
    confusion_df: pd.DataFrame = evaluation.get("confusion_df", pd.DataFrame())

    return {
        "metrics_df": to_serializable(metrics_df.to_dict(orient="records")),
        "intent_breakdown": to_serializable(intent_breakdown.to_dict(orient="records")) if not intent_breakdown.empty else [],
        "entity_breakdown": to_serializable(entity_breakdown.to_dict(orient="records")) if not entity_breakdown.empty else [],
        "confusion_df": to_serializable(confusion_df.to_dict(orient="records")) if not confusion_df.empty else [],
    }


def deserialize_analysis_from_api(data: Dict[str, Any]) -> Dict[str, Any]:
    """Deserialize analysis results from API"""
    sample_df = pd.DataFrame(data.get("sample") or [])
    intent_distribution = pd.DataFrame(data.get("intent_distribution") or [])
    entity_distribution = pd.DataFrame(data.get("entity_distribution") or [])

    return {
        "stats": data.get("stats", {}),
        "sample": sample_df,
        "intent_columns": data.get("intent_columns", []),
        "entity_columns": data.get("entity_columns", []),
        "intents": data.get("intents", []),
        "entities": data.get("entities", []),
        "intent_distribution": intent_distribution,
        "entity_distribution": entity_distribution,
    }


def deserialize_evaluation_from_api(data: Dict[str, Any]) -> Dict[str, Any]:
    """Deserialize evaluation results from API"""
    metrics_df = pd.DataFrame(data.get("metrics_df") or [])
    intent_breakdown = pd.DataFrame(data.get("intent_breakdown") or [])
    entity_breakdown = pd.DataFrame(data.get("entity_breakdown") or [])
    confusion_df = pd.DataFrame(data.get("confusion_df") or [])

    download_csv = metrics_df.to_csv(index=False).encode("utf-8") if not metrics_df.empty else b"Metric,Value\n"

    return {
        "metrics_df": metrics_df,
        "intent_breakdown": intent_breakdown,
        "entity_breakdown": entity_breakdown,
        "confusion_df": confusion_df,
        "download_csv": download_csv,
    }


def parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO timestamp string"""
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00") if isinstance(value, str) else value
        if isinstance(normalized, str):
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
    except Exception:
        return None
    return None


def format_timestamp(value: Optional[str]) -> str:
    """Format timestamp for display"""
    parsed = parse_iso_timestamp(value)
    if not parsed:
        return str(value) if value else "Unknown timestamp"
    return parsed.strftime("%b %d, %Y %I:%M %p")


def process_dataset(uploaded_file) -> bool:
    """Process uploaded dataset file"""
    progress = st.progress(0)
    try:
        with st.spinner("Processing dataset..."):
            raw_bytes = uploaded_file.read()
            if not raw_bytes:
                raise ValueError("Uploaded file is empty.")

            progress.progress(20)
            name_lower = uploaded_file.name.lower()
            mime = uploaded_file.type or ""

            if name_lower.endswith(".json") or "json" in mime:
                text = raw_bytes.decode("utf-8")
                progress.progress(45)
                data = json.loads(text)
                if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                    data = data["data"]
                df = pd.json_normalize(data)
            else:
                df = pd.read_csv(BytesIO(raw_bytes))

            progress.progress(70)
            if df.empty:
                raise ValueError("Dataset is empty after parsing.")

            df = df.replace({np.nan: None})
            analysis = analyze_dataframe(df)
            evaluation = simulate_evaluation(df, analysis)

            st.session_state["dataset_df"] = df
            st.session_state["dataset_analysis"] = analysis
            st.session_state["evaluation_results"] = evaluation
            st.session_state["uploaded_filename"] = uploaded_file.name

            from dataset_manager import save_dataset_state, load_persisted_dataset
            saved_payload = save_dataset_state(uploaded_file.name, analysis, evaluation)
            if saved_payload:
                load_persisted_dataset(force=True)

            progress.progress(100)
            return True
    except Exception as exc:
        progress.progress(0)
        st.error(f"Failed to process dataset: {exc}")
        return False
    finally:
        uploaded_file.seek(0)
