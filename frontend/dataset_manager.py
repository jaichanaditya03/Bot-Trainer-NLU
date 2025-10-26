"""
Dataset state management and persistence
"""
import streamlit as st
import pandas as pd
from api_client import api_post, api_get, humanize_error
from utils import (
    serialize_analysis_for_api, 
    serialize_evaluation_for_api,
    deserialize_analysis_from_api,
    deserialize_evaluation_from_api
)


def save_dataset_state(filename: str, analysis: dict, evaluation: dict):
    """Save dataset analysis to backend"""
    if not st.session_state.get("token"):
        return

    payload = {
        "filename": filename,
        "analysis": serialize_analysis_for_api(analysis),
        "evaluation": serialize_evaluation_for_api(evaluation),
        "checksum": analysis.get("checksum") or evaluation.get("checksum"),
    }

    data, status = api_post("/datasets", json=payload, auth_required=True)
    if status not in (200, 201):
        st.warning(f"⚠️ Unable to save dataset: {humanize_error(data)}")
        return None

    checksum = data.get("checksum") if isinstance(data, dict) else None
    if checksum:
        payload["checksum"] = checksum
    st.session_state["selected_dataset_checksum"] = payload.get("checksum")
    return payload


def load_persisted_dataset(force: bool = False):
    """Load saved datasets from backend"""
    if not st.session_state.get("token"):
        return
    if not force and st.session_state.get("dataset_analysis"):
        return

    data, status = api_get("/datasets", auth_required=True)
    if status == 200 and data:
        selected = data.get("selected") or {}
        entries = data.get("entries") or []
        analysis = deserialize_analysis_from_api(selected.get("analysis", {})) if selected else None
        evaluation = deserialize_evaluation_from_api(selected.get("evaluation", {})) if selected else None

        st.session_state["dataset_analysis"] = analysis
        st.session_state["evaluation_results"] = evaluation
        st.session_state["uploaded_filename"] = selected.get("filename") if selected else None
        st.session_state["selected_dataset_checksum"] = selected.get("checksum") if selected else None
        st.session_state["uploaded_history"] = entries
        if analysis:
            sample_df = analysis.get("sample")
            st.session_state["dataset_df"] = sample_df if isinstance(sample_df, pd.DataFrame) else pd.DataFrame(sample_df or [])
            analysis["checksum"] = selected.get("checksum")
        else:
            st.session_state["dataset_df"] = None
    elif status >= 400:
        st.warning(f"⚠️ Unable to load saved dataset: {humanize_error(data)}")


def select_saved_dataset(checksum: str) -> bool:
    """Select a dataset from history"""
    if not st.session_state.get("token"):
        st.warning("Please login to select a dataset.")
        return False

    data, status = api_post("/datasets/select", json={"checksum": checksum}, auth_required=True)
    if status == 200:
        load_persisted_dataset(force=True)
        return True

    st.warning(f"⚠️ Unable to load selected dataset: {humanize_error(data)}")
    return False
