import json
from collections import Counter
from datetime import datetime, timezone
from io import BytesIO
from time import sleep
import re
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx  # type: ignore
except ImportError:  # Streamlit versions without the helper
    get_script_run_ctx = None  # type: ignore

# ---------------- CONFIG ----------------
API_BASE = "http://127.0.0.1:8000"
st.set_page_config(
    page_title="Bot Trainer Application",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded",
)

BACKGROUND_CSS = """
<style>
:root {
    --glass-bg: rgba(6, 18, 32, 0.65);
    --glass-border: rgba(142, 228, 175, 0.25);
    --accent: #32f47a;
    --accent-dark: #0b3d21;
}


[data-testid="stToolbar"] {
    background: transparent !important;
}

[data-testid="stCollapsedControl"] button {
    border: none !important;
    background: rgba(5, 15, 27, 0.78) !important;
    color: #f3fbff !important;
}

[data-testid="stStatusWidget"] {
    display: none !important;
}

[data-testid="stHeaderActionContainer"] button[title="View fullscreen"],
[data-testid="stHeaderActionContainer"] button[title="Rerun"] {
    display: none !important;
}

.stApp {
    background: transparent;
    color: #f5f9ff;
}

.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    background: url('https://images.hdqwalls.com/download/graph-web-abstract-4k-hn-1920x1080.jpg') no-repeat center center fixed;
    background-size: cover;
    z-index: -2;
    animation: hueShift 16s linear infinite;
    filter: hue-rotate(0deg) saturate(1.1);
}

.stApp::after {
    content: "";
    position: fixed;
    inset: 0;
    background: radial-gradient(circle at 20% 20%, rgba(46, 255, 146, 0.15), transparent 45%),
                radial-gradient(circle at 80% 10%, rgba(46, 186, 255, 0.12), transparent 40%),
                linear-gradient(135deg, rgba(2, 12, 22, 0.6), rgba(0, 0, 0, 0.75));
    z-index: -1;
    backdrop-filter: blur(2px);
}

@keyframes hueShift {
    0% { filter: hue-rotate(0deg) saturate(1.1); }
    50% { filter: hue-rotate(180deg) saturate(1.3); }
    100% { filter: hue-rotate(360deg) saturate(1.1); }
}

.hero-intro {
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    align-items: center;
    margin-bottom: 1.5rem;
}

.hero-intro h1 {
    font-size: clamp(2.6rem, 5vw, 3.4rem);
    font-weight: 700;
    letter-spacing: 0.015em;
    margin: 0;
}

.hero-intro p {
    font-size: 1.1rem;
    line-height: 1.6;
    max-width: 36rem;
    color: rgba(228, 247, 238, 0.85);
}

main .block-container {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 28px;
    padding: 3.5rem 3rem 4rem;
    box-shadow: 0 35px 80px rgba(0, 0, 0, 0.55);
    backdrop-filter: blur(18px);
    max-width: 720px;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.8rem;
    background: rgba(4, 14, 18, 0.6);
    padding: 0.6rem;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.stTabs [data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    color: #f2f9ff;
    font-weight: 600;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: rgba(50, 244, 122, 0.22);
    color: #0b1f12;
    box-shadow: inset 0 0 0 1px rgba(50, 244, 122, 0.45);
}

.stDownloadButton > button {
    background: linear-gradient(120deg, #2a9df4, #1cf6cf);
    color: #031421;
    border: none;
    border-radius: 999px;
    padding: 0.55rem 1.4rem;
    font-weight: 600;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 18px 36px rgba(28, 246, 207, 0.35);
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, #32f47a, #29c6f0);
}

main .block-container h1,
main .block-container h2,
main .block-container h3,
main .block-container p,
main .block-container label,
main .block-container span,
main .block-container .stMarkdown,
main .block-container .st-success,
main .block-container .st-warning,
main .block-container .st-error {
    color: #f3f8ff !important;
}

[data-testid="stSidebar"] {
    background: rgba(5, 15, 27, 0.78) !important;
    backdrop-filter: blur(18px);
    border-right: 1px solid rgba(142, 228, 175, 0.18);
}

[data-testid="stSidebar"] * {
    color: #f3fbff !important;
}

[data-baseweb="radio"] div[role="radiogroup"]>div {
    background: rgba(255, 255, 255, 0.04);
    border-radius: 14px;
    padding: 0.4rem 0.6rem;
}

[data-baseweb="radio"] label {
    border-radius: 10px;
    padding: 0.35rem 0.8rem;
}

[data-baseweb="radio"] label[data-checked="true"] {
    background: rgba(50, 244, 122, 0.25);
    border: 1px solid rgba(50, 244, 122, 0.35);
}

div[data-baseweb="input"] {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.18);
    transition: border 0.2s ease, box-shadow 0.2s ease;
}

div[data-baseweb="input"]:focus-within {
    border-color: rgba(50, 244, 122, 0.55);
    box-shadow: 0 8px 24px rgba(50, 244, 122, 0.15);
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    color: #f7fbff !important;
}

textarea {
    background: rgba(255, 255, 255, 0.04) !important;
    border-radius: 18px !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    color: #f7fbff !important;
}

.stButton>button {
    width: 100%;
    border-radius: 999px;
    padding: 0.6rem 1.2rem;
    background: linear-gradient(120deg, #2bf06f, #1bc861);
    color: #04130a;
    font-weight: 600;
    letter-spacing: 0.02em;
    border: none;
    box-shadow: 0 18px 32px rgba(41, 224, 113, 0.25);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 26px 40px rgba(41, 224, 113, 0.35);
}

.stButton>button:active {
    transform: translateY(0);
}

.st-bw {
    background-color: rgba(4, 18, 15, 0.45) !important;
}

.st-alert {
    border-radius: 16px;
    background-color: rgba(13, 33, 24, 0.65);
}

@media (max-width: 768px) {
    main .block-container {
        padding: 2.4rem 1.6rem 3rem;
        margin: 2.4rem 0;
    }
}
</style>
"""

st.markdown(BACKGROUND_CSS, unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "token" not in st.session_state:
    st.session_state["token"] = None
if "email" not in st.session_state:
    st.session_state["email"] = None
if "username" not in st.session_state:
    st.session_state["username"] = None
if "page" not in st.session_state:
    st.session_state["page"] = "Home"
if "dataset_df" not in st.session_state:
    st.session_state["dataset_df"] = None
if "dataset_analysis" not in st.session_state:
    st.session_state["dataset_analysis"] = None
if "evaluation_results" not in st.session_state:
    st.session_state["evaluation_results"] = None
if "uploaded_filename" not in st.session_state:
    st.session_state["uploaded_filename"] = None
if "uploaded_history" not in st.session_state:
    st.session_state["uploaded_history"] = []
if "selected_dataset_checksum" not in st.session_state:
    st.session_state["selected_dataset_checksum"] = None
if "processed_upload_token" not in st.session_state:
    st.session_state["processed_upload_token"] = None


def get_sidebar_toggle_state() -> bool:
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
            # Fallback for implementations that expose dict-like get
            return bool(getattr(state, "get", lambda *_, **__: False)("_sidebar_toggled", False))
        except Exception:
            return False


def set_page(page: str):
    st.session_state["page"] = page


def nav_options():
    if st.session_state.get("token"):
        return ["Home", "Dashboard", "Logout"]
    return ["Home", "Register", "Login"]

# ---------------- HELPER FUNCTIONS ----------------
def api_post(path, json=None, auth_required=False):
    headers = {}
    if auth_required and st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state['token']}"
    try:
        resp = requests.post(f"{API_BASE}{path}", json=json, headers=headers)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def api_get(path, auth_required=False):
    headers = {}
    if auth_required and st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state['token']}"
    try:
        resp = requests.get(f"{API_BASE}{path}", headers=headers)
        return resp.json(), resp.status_code
    except Exception as e:
        return {"error": str(e)}, 500


def humanize_error(payload):
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


def _normalize_value(value, split_tokens=False):
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


def analyze_dataframe(df: pd.DataFrame):
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


def simulate_evaluation(df: pd.DataFrame, analysis: dict):
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
    try:
        return json.loads(json.dumps(data, default=str))
    except TypeError:
        return data


def serialize_analysis_for_api(analysis: Dict[str, Any]) -> Dict[str, Any]:
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


def save_dataset_state(filename: str, analysis: Dict[str, Any], evaluation: Dict[str, Any]):
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
    if not st.session_state.get("token"):
        st.warning("Please login to select a dataset.")
        return False

    data, status = api_post("/datasets/select", json={"checksum": checksum}, auth_required=True)
    if status == 200:
        load_persisted_dataset(force=True)
        return True

    st.warning(f"⚠️ Unable to load selected dataset: {humanize_error(data)}")
    return False


def format_timestamp(value: Optional[str]) -> str:
    parsed = parse_iso_timestamp(value)
    if not parsed:
        return str(value) if value else "Unknown timestamp"
    return parsed.strftime("%b %d, %Y %I:%M %p")


def parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
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


def process_dataset(uploaded_file) -> bool:
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

# ---------------- CUSTOM JS FOR ENTER NAVIGATION ----------------
enter_js = """
<script>
const hideApplyHints = () => {
    const candidates = [
        ...document.querySelectorAll('[data-testid="textInputInstructions"]'),
        ...document.querySelectorAll('[data-testid="stTooltipLabel"]'),
       # ...document.querySelectorAll('[aria-label="Press Enter to apply"]')
    ];
    candidates.forEach(el => {
        if (el && typeof el.textContent === 'string' && el.textContent.toLowerCase().includes('press enter to apply')) {
            el.style.display = 'none';
        }
        if (el && el.parentElement && el.parentElement.getAttribute('aria-label') === 'Press Enter to apply') {
            el.parentElement.style.display = 'none';
        }
    });
};

const triggerPrimaryButton = (startEl) => {
    if (!startEl) {
        startEl = document.activeElement;
    }
    const container = startEl ? startEl.closest('[data-testid="stVerticalBlock"]') : null;
    const searchScope = container || document;
    const buttons = Array.from(searchScope.querySelectorAll('button'));
    const preferredLabels = ['login', 'register', 'submit', 'continue', 'save', 'load'];
    const match = buttons.find((btn) => {
        const text = (btn.innerText || '').trim().toLowerCase();
        if (!text) return false;
        if (preferredLabels.includes(text)) return true;
        return btn.getAttribute('kind') === 'primary';
    });
    if (match) {
        match.click();
        return true;
    }
    return false;
};

const attachEnterHandlers = () => {
    const inputs = Array.from(document.querySelectorAll('input[type=text], input[type=email], input[type=password]'));
    inputs.forEach((input, index) => {
        if (input.dataset.enterHandlerBound === 'true') {
            return;
        }
        input.dataset.enterHandlerBound = 'true';
        input.addEventListener('keydown', (event) => {
            if (event.key !== 'Enter') {
                return;
            }

            const next = inputs[index + 1];
            if (next) {
                event.preventDefault();
                next.focus();
                return;
            }

            if (triggerPrimaryButton(input)) {
                event.preventDefault();
            }
        }, { once: false });
    });
};

const combinedObserver = new MutationObserver(() => {
    hideApplyHints();
    attachEnterHandlers();
});

combinedObserver.observe(document.body, { childList: true, subtree: true });
hideApplyHints();
attachEnterHandlers();
</script>
"""

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712027.png", width=80)
    st.markdown("### 🤖 Bot Trainer App")
    options = nav_options()
    current_page = st.session_state.get("page", options[0])
    if current_page not in options:
        current_page = options[0]
    menu = st.radio(
        "Navigate",
        options,
        index=options.index(current_page),
        key="nav_menu",
    )
    if menu != st.session_state.get("page"):
        set_page(menu)

page = st.session_state.get("page", "Home")
sidebar_state = get_sidebar_toggle_state()

# ---------------- HOME PAGE ----------------
if page == "Home":
    st.markdown(enter_js, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero-intro">
            <h1>Welcome to Bot Trainer Application 🤖</h1>
            <p>Design, launch, and manage conversational projects in a single secure workspace. Register or log in to start training bots tailored to your team.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cta_cols = st.columns(2)
    create_clicked = False
    login_clicked = False
    with cta_cols[0]:
        if st.button("Create an account", use_container_width=True):
            create_clicked = True
    with cta_cols[1]:
        if st.button("Access your workspace", use_container_width=True):
            login_clicked = True

    if create_clicked:
        set_page("Register")
        st.rerun()
    if login_clicked:
        set_page("Login")
        st.rerun()

# ---------------- REGISTER PAGE ----------------
elif page == "Register":
    st.title("Create Account 🧾")
    st.markdown(enter_js, unsafe_allow_html=True)

    username = st.text_input("👤 Username")
    email = st.text_input("📧 Email")
    password = st.text_input("🔐 Password", type="password")

    submitted = st.button("Register")

    if submitted:
        if not username or not email or not password:
            st.warning("⚠️ Please fill in all fields.")
        elif len(password) < 6 or not re.search(r"[^\w\s]", password):
            st.warning("⚠️ Password must be at least 6 characters and include a special character.")
        else:
            with st.spinner("Registering..."):
                payload = {
                    "username": username.strip(),
                    "email": email.strip(),
                    "password": password,
                }
                data, status = api_post("/register", json=payload)
                sleep(0.8)
                if status in (200, 201):
                    st.balloons()
                    st.success("✅ Registration successful! Redirecting to login...")
                    sleep(1)
                    set_page("Login")
                    st.rerun()
                else:
                    st.error(f"❌ {humanize_error(data)}")

# ---------------- LOGIN PAGE ----------------
elif page == "Login":
    st.title("Login 🔑")
    st.markdown(enter_js, unsafe_allow_html=True)

    email = st.text_input("📧 Email", key="login_email")
    password = st.text_input("🔐 Password", type="password", key="login_pass")

    submitted = st.button("Login")

    if submitted:
        if not email or not password:
            st.warning("⚠️ Please fill in all fields.")
        else:
            with st.spinner("Verifying credentials..."):
                payload = {"email": email, "password": password}
                data, status = api_post("/login", json=payload)
                sleep(0.8)
                if status == 200:
                    st.session_state["token"] = data.get("access_token")
                    st.session_state["email"] = email
                    st.session_state["username"] = data.get("username")
                    load_persisted_dataset(force=True)
                    display_name = st.session_state["username"] or email
                    st.success(f"🎉 Welcome back, {display_name}")
                    sleep(1)
                    set_page("Dashboard")  # ✅ redirect to dashboard
                    st.rerun()
                else:
                    st.error(f"❌ Login failed: {humanize_error(data)}")

# ---------------- DASHBOARD ----------------
elif page == "Dashboard":
    st.title("Dashboard 📊")
    st.markdown(enter_js, unsafe_allow_html=True)

    if not st.session_state.get("token"):
        st.warning("Please login to access the dashboard.")
    else:
        if not st.session_state.get("dataset_analysis"):
            load_persisted_dataset()
        display_name = st.session_state.get("username") or st.session_state.get("email")
        st.success(f"Welcome, **{display_name}** 👋")
        st.markdown("---")

        tab_upload, tab_overview, tab_evaluate = st.tabs(["Upload Data", "View Data", "Evaluate"])

        with tab_upload:
            st.subheader("Upload Training Dataset")
            st.caption("Supported formats: CSV and JSON")
            uploaded_file = st.file_uploader("Drop or browse a dataset", type=["csv", "json"], accept_multiple_files=False)

            if uploaded_file is not None:
                file_token = f"{uploaded_file.name}:{getattr(uploaded_file, 'size', 'na')}:{uploaded_file.type}"
                if st.session_state.get("processed_upload_token") != file_token:
                    if process_dataset(uploaded_file):
                        st.session_state["processed_upload_token"] = file_token
                        st.success(f"✅ Processed `{uploaded_file.name}` successfully.")
                    else:
                        st.info("Upload a new file to try again.")
                else:
                    st.caption(f"`{uploaded_file.name}` already processed. Remove and re-upload to process again.")
            else:
                if st.session_state.get("processed_upload_token"):
                    st.session_state["processed_upload_token"] = None
                last_file = st.session_state.get("uploaded_filename")
                if last_file:
                    st.caption(f"Last processed file: `{last_file}`")

            history_entries = st.session_state.get("uploaded_history") or []
            selected_checksum = st.session_state.get("selected_dataset_checksum")
            if history_entries:
                # Remove duplicates by filename while keeping most recent per file
                unique_by_filename: Dict[str, Dict[str, Any]] = {}
                for entry in history_entries:
                    filename = entry.get("filename") or ""
                    timestamp = parse_iso_timestamp(entry.get("updated_at")) or datetime.min
                    existing = unique_by_filename.get(filename)
                    if not existing:
                        unique_by_filename[filename] = {"entry": entry, "timestamp": timestamp}
                        continue
                    if timestamp >= existing["timestamp"]:
                        unique_by_filename[filename] = {"entry": entry, "timestamp": timestamp}

                unique_entries = sorted(
                    (payload["entry"] for payload in unique_by_filename.values()),
                    key=lambda item: parse_iso_timestamp(item.get("updated_at")) or datetime.min,
                    reverse=True,
                )

                st.markdown("#### Recent Datasets")
                for index, entry in enumerate(unique_entries):
                    checksum_value = entry.get("checksum")
                    checksum_key = checksum_value or f"history-{index}"
                    filename = entry.get("filename") or "Untitled dataset"
                    stats = (entry.get("analysis") or {}).get("stats") or {}
                    rows = stats.get("rows")
                    cols = stats.get("columns")
                    meta_bits = []
                    if rows is not None:
                        meta_bits.append(f"{rows} rows")
                    if cols is not None:
                        meta_bits.append(f"{cols} columns")
                    timestamp_label = format_timestamp(entry.get("updated_at"))
                    is_active = checksum_value and checksum_value == selected_checksum

                    box = st.container()
                    with box:
                        col_info, col_action = st.columns([0.7, 0.3])
                        with col_info:
                            title = f"✅ **{filename}**" if is_active else f"**{filename}**"
                            st.markdown(title)
                            st.caption(f"Last processed: {timestamp_label}")
                            if meta_bits:
                                st.caption(" | ".join(meta_bits))
                        with col_action:
                            button_label = "Active" if is_active else "Load"
                            disabled = is_active or not checksum_value
                            if st.button(button_label, key=f"history_btn_{checksum_key}", disabled=disabled):
                                if checksum_value and select_saved_dataset(checksum_value):
                                    st.success(f"Loaded `{filename}` from history.")
                                    st.rerun()

        with tab_overview:
            st.subheader("Dataset Overview")
            df = st.session_state.get("dataset_df")
            analysis = st.session_state.get("dataset_analysis")

            if df is None or analysis is None:
                st.info("Upload and process a dataset in the **Upload Data** tab to view its structure.")
            else:
                cols_top = st.columns(4)
                cols_top[0].metric("Rows", analysis["stats"]["rows"])
                cols_top[1].metric("Columns", analysis["stats"]["columns"])
                cols_top[2].metric("Detected Intents", len(analysis["intents"]))
                cols_top[3].metric("Detected Entities", len(analysis["entities"]))

                st.divider()
                st.caption("Detected intent columns")
                st.write(", ".join(analysis["intent_columns"]) or "None detected")
                st.caption("Detected entity columns")
                st.write(", ".join(analysis["entity_columns"]) or "None detected")

                st.markdown("#### Sample Records")
                st.dataframe(analysis["sample"], use_container_width=True, height=320)

                st.markdown("#### Intent Distribution")
                if not analysis["intent_distribution"].empty:
                    fig_intents = px.bar(analysis["intent_distribution"], x="Intent", y="Count", color="Count", color_continuous_scale="Viridis")
                    fig_intents.update_layout(margin=dict(l=16, r=16, t=32, b=16))
                    st.plotly_chart(fig_intents, use_container_width=True)
                else:
                    st.info("No intents detected in dataset.")

                st.markdown("#### Entity Distribution")
                if not analysis["entity_distribution"].empty:
                    fig_entities = px.bar(analysis["entity_distribution"], x="Entity", y="Count", color="Count", color_continuous_scale="Bluered")
                    fig_entities.update_layout(margin=dict(l=16, r=16, t=32, b=16))
                    st.plotly_chart(fig_entities, use_container_width=True)
                else:
                    st.info("No entities detected in dataset.")

                st.markdown("#### Search / Filter Intents")
                search_term = st.text_input("Filter by intent name")
                filtered_intents = [intent for intent in analysis["intents"] if search_term.lower() in intent.lower()] if search_term else analysis["intents"]
                st.write(filtered_intents or "No intents match your filter.")

        with tab_evaluate:
            st.subheader("Evaluation Snapshot")
            evaluation = st.session_state.get("evaluation_results")

            if evaluation is None:
                st.info("Upload a dataset to generate evaluation metrics.")
            else:
                metrics_df = evaluation["metrics_df"]
                st.dataframe(metrics_df, use_container_width=True, height=200)

                cols_eval = st.columns(3)
                for col, row in zip(cols_eval, metrics_df.itertuples()):
                    col.metric(row.Metric, f"{row.Value}%")

                st.markdown("#### Accuracy Overview")
                fig_metrics = px.bar(metrics_df, x="Metric", y="Value", color="Metric", text="Value", color_discrete_sequence=px.colors.qualitative.Set2)
                fig_metrics.update_traces(texttemplate="%{y}%", textposition="outside")
                fig_metrics.update_layout(yaxis=dict(range=[0, 100]), margin=dict(l=16, r=16, t=32, b=16))
                st.plotly_chart(fig_metrics, use_container_width=True)

                st.markdown("#### Intent Breakdown")
                if not evaluation["intent_breakdown"].empty:
                    fig_intent_breakdown = px.bar(evaluation["intent_breakdown"], x="Intent", y="Accuracy", color="Accuracy", color_continuous_scale="Aggrnyl")
                    fig_intent_breakdown.update_layout(yaxis=dict(range=[0, 100]), margin=dict(l=16, r=16, t=32, b=16))
                    st.plotly_chart(fig_intent_breakdown, use_container_width=True)
                else:
                    st.info("No intents available for breakdown.")

                st.markdown("#### Entity Extraction Breakdown")
                if not evaluation["entity_breakdown"].empty:
                    fig_entity_breakdown = px.bar(evaluation["entity_breakdown"], x="Entity", y="Extraction Accuracy", color="Extraction Accuracy", color_continuous_scale="Sunset")
                    fig_entity_breakdown.update_layout(yaxis=dict(range=[0, 100]), margin=dict(l=16, r=16, t=32, b=16))
                    st.plotly_chart(fig_entity_breakdown, use_container_width=True)
                else:
                    st.info("No entities available for breakdown.")

                st.markdown("#### Confusion Rate")
                fig_confusion = px.pie(evaluation["confusion_df"], names="Outcome", values="Value", color="Outcome", color_discrete_map={"Correct": "#2fdd92", "Confused": "#ff7b7b"})
                fig_confusion.update_layout(margin=dict(l=16, r=16, t=16, b=16))
                st.plotly_chart(fig_confusion, use_container_width=True)

                st.download_button(
                    "⬇️ Export Evaluation Metrics",
                    data=evaluation["download_csv"],
                    file_name=f"evaluation-metrics-{display_name or 'user'}.csv",
                    mime="text/csv",
                )

# ---------------- LOGOUT ----------------
elif page == "Logout":
    st.session_state["token"] = None
    st.session_state["email"] = None
    st.session_state["username"] = None
    st.session_state["dataset_df"] = None
    st.session_state["dataset_analysis"] = None
    st.session_state["evaluation_results"] = None
    st.session_state["uploaded_filename"] = None
    set_page("Home")
    st.success("✅ You have been logged out successfully.")
    sleep(1)
    st.rerun()
