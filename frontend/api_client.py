"""
API client utilities for backend communication
"""
import requests
import streamlit as st
from config import API_BASE


def api_post(path: str, json=None, auth_required: bool = False):
    """
    Make POST request to backend API
    
    Args:
        path: API endpoint path
        json: JSON payload
        auth_required: Whether authentication is required
        
    Returns:
        Tuple of (response_data, status_code)
    """
    headers = {}
    if auth_required and st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state['token']}"
    try:
        resp = requests.post(f"{API_BASE}{path}", json=json, headers=headers)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 500


def api_get(path: str, auth_required: bool = False):
    """
    Make GET request to backend API
    
    Args:
        path: API endpoint path
        auth_required: Whether authentication is required
        
    Returns:
        Tuple of (response_data, status_code)
    """
    headers = {}
    if auth_required and st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state['token']}"
    try:
        resp = requests.get(f"{API_BASE}{path}", headers=headers)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 500


def humanize_error(payload) -> str:
    """
    Convert API error response to human-readable message
    
    Args:
        payload: Error response from API
        
    Returns:
        Human-readable error string
    """
    detail = None
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("error")
    if not detail:
        detail = payload

    if isinstance(detail, list):
        messages = []
        for item in detail:
            if isinstance(item, dict):
                loc = item.get("loc", [])
                field = loc[-1] if loc else ""
                msg = item.get("msg") or item.get("detail") or str(item)
                if field and isinstance(field, str):
                    messages.append(f"{field.capitalize()}: {msg}")
                else:
                    messages.append(msg)
            else:
                messages.append(str(item))
        return "\n".join(messages)

    if isinstance(detail, dict):
        return detail.get("msg") or detail.get("detail") or str(detail)

    return str(detail)
