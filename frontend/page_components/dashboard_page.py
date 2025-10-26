"""
Dashboard page with dataset management tabs
"""
from datetime import datetime
from typing import Any, Dict
import streamlit as st
import plotly.express as px

from styles import ENTER_NAVIGATION_JS
from utils import process_dataset, format_timestamp, parse_iso_timestamp
from dataset_manager import load_persisted_dataset, select_saved_dataset


def render_dashboard_page():
    """Render the main dashboard"""
    st.title("Dashboard 📊")
    st.markdown(ENTER_NAVIGATION_JS, unsafe_allow_html=True)

    if not st.session_state.get("token"):
        st.warning("Please login to access the dashboard.")
        return

    if not st.session_state.get("dataset_analysis"):
        load_persisted_dataset()
    
    display_name = st.session_state.get("username") or st.session_state.get("email")
    st.success(f"Welcome, **{display_name}** 👋")
    st.markdown("---")

    tab_upload, tab_overview, tab_evaluate = st.tabs(["Upload Data", "View Data", "Evaluate"])

    with tab_upload:
        render_upload_tab()

    with tab_overview:
        render_overview_tab()

    with tab_evaluate:
        render_evaluate_tab()


def render_upload_tab():
    """Render upload data tab"""
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

    # Dataset history
    render_dataset_history()


def render_dataset_history():
    """Render dataset history section"""
    history_entries = st.session_state.get("uploaded_history") or []
    selected_checksum = st.session_state.get("selected_dataset_checksum")
    
    if not history_entries:
        return

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


def render_overview_tab():
    """Render dataset overview tab"""
    st.subheader("Dataset Overview")
    df = st.session_state.get("dataset_df")
    analysis = st.session_state.get("dataset_analysis")

    if df is None or analysis is None:
        st.info("Upload and process a dataset in the **Upload Data** tab to view its structure.")
        return

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


def render_evaluate_tab():
    """Render evaluation tab"""
    st.subheader("Evaluation Snapshot")
    evaluation = st.session_state.get("evaluation_results")
    display_name = st.session_state.get("username") or st.session_state.get("email")

    if evaluation is None:
        st.info("Upload a dataset to generate evaluation metrics.")
        return

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
