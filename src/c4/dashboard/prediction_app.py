"""C4 Digital Forensic Investigation Prototype - Streamlit Dashboard with Prediction Panel (FR1-FR9, NFR4, NFR6)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

# Add src to path
SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from c4.dashboard.charts import create_chronological_timeline_chart
from c4.dashboard.export_utils import export_timeline_to_csv, export_timeline_to_json
from c4.dashboard.loaders import MissingArtifactError, load_dashboard_data
from c4.dashboard.prediction_panel import (
    extract_panel_view_data,
    get_records_by_episode,
    load_prediction_records_by_sample,
    render_prediction_panel_html,
    render_prediction_panel_streamlit,
)
from c4.timeline import C3_FIELDS, filter_timeline

# ---------------------------------------------------------------------------
# Streamlit Page Config & Styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="C4 Forensic Investigation & Prediction Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge-gt {
        background-color: #DCFCE7;
        color: #166534;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .badge-derived {
        background-color: #DBEAFE;
        color: #1E40AF;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .badge-missing {
        background-color: #FEE2E2;
        color: #991B1B;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_dashboard() -> None:
    # -----------------------------------------------------------------------
    # Data Loading (Reads preprocessed artifacts; no pipeline logic in UI)
    # -----------------------------------------------------------------------
    try:
        data = load_dashboard_data()
    except MissingArtifactError as exc:
        st.error(f"### ⚠️ Data Artifacts Missing\n\n{exc}")
        st.stop()
        return

    timelines = data["timelines"]
    sequences = data["sequences"]
    data_quality = data["data_quality"]
    discrepancies = data["tactic_discrepancies"]
    wazuh_alerts_df = data["wazuh_alerts_df"]

    episodes = list(timelines.keys())
    ep_summaries = data_quality.get("episodes", {})

    # Load prediction records
    try:
        records_by_sample = load_prediction_records_by_sample()
        records_by_ep = get_records_by_episode()
    except Exception as exc:
        records_by_sample = {}
        records_by_ep = {}

    # -----------------------------------------------------------------------
    # Sidebar: Episode Selector & Run Metadata
    # -----------------------------------------------------------------------
    st.sidebar.title("🛡️ C4 Forensic Prototype")
    st.sidebar.caption("CTI-Assisted Forensic Timeline Reconstruction & Prediction")

    st.sidebar.markdown("---")
    st.sidebar.subheader("Select Attack Episode")
    selected_ep = st.sidebar.selectbox("Active Episode", episodes, index=0)

    ep_meta = ep_summaries.get(selected_ep, {})
    st.sidebar.markdown(
        f"""
        <div class="metric-card">
            <b>Scenario:</b> <code>{ep_meta.get('scenario_id', 'N/A')}</code><br>
            <b>Archive:</b> <code>{ep_meta.get('source_archive', 'N/A')}</code><br>
            <b>Window Start:</b> <code>{ep_meta.get('window_start', 'N/A')}</code><br>
            <b>Window End:</b> <code>{ep_meta.get('window_end', 'N/A')}</code><br>
            <b>Total Events:</b> {ep_meta.get('total_events', len(timelines.get(selected_ep, [])))}<br>
            <b>Labeled Events:</b> {ep_meta.get('labeled_events', 'N/A')}<br>
            <b>Unlabeled Events:</b> {ep_meta.get('unlabeled_events', 'N/A')}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.info("🔒 **Strict Isolation:** Episodes represent distinct simulation runs and are never merged.")

    # -----------------------------------------------------------------------
    # Main Navigation Tabs
    # -----------------------------------------------------------------------
    tabs = st.tabs([
        "1. Overview",
        "2. Episode Timeline",
        "3. ATT&CK Sequences",
        "4. Next-Step Prediction (FR6-FR9)",
        "5. Tactic Discrepancies",
        "6. Data Quality & C3",
        "7. Wazuh Telemetry",
        "8. Export Data",
    ])

    # =======================================================================
    # Tab 1: Overview
    # =======================================================================
    with tabs[0]:
        st.header("Campaign Overview & Telemetry Summary")

        dq_summary = data_quality.get("summary", {})
        total_events = dq_summary.get("total_events", sum(len(t) for t in timelines.values()))
        total_labeled = dq_summary.get("total_labeled", 0)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Episodes Tracked", len(episodes))
        col2.metric("Total Forensic Events", total_events)
        col3.metric("Labeled Actions", total_labeled)
        col4.metric("Prediction Samples", len(records_by_sample))

        st.markdown("### Campaign Telemetry Status")
        st.info("Component 4 reconstructs chronological event timelines from forensic host telemetry and generates explainable next-step predictions.")

    # =======================================================================
    # Tab 2: Episode Timeline
    # =======================================================================
    with tabs[1]:
        st.header(f"Forensic Timeline: {selected_ep}")
        ep_events = timelines.get(selected_ep, [])
        if ep_events:
            fig = create_chronological_timeline_chart(ep_events, y_axis_mode="technique")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(pd.DataFrame(ep_events))
        else:
            st.warning("No events found for selected episode.")

    # =======================================================================
    # Tab 3: ATT&CK Sequences
    # =======================================================================
    with tabs[2]:
        st.header(f"Reconstructed Attack Sequences: {selected_ep}")
        ep_seq = sequences.get(selected_ep, {})
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Raw Sequence (Event-aligned)")
            st.json(ep_seq.get("raw", []))
        with col2:
            st.subheader("Collapsed Sequence (Consecutive deduplicated)")
            st.json(ep_seq.get("collapsed", []))

    # =======================================================================
    # Tab 4: Next-Step Prediction (FR6, FR7, FR9, NFR4, NFR6)
    # =======================================================================
    with tabs[3]:
        st.header("Forensic Next-Step Attack Prediction (Demo Mode)")
        st.caption("Reads precomputed LOEO prediction records (FR4-FR7). Zero UI runtime calculation.")

        ep_records = records_by_ep.get(selected_ep, [])
        if not ep_records:
            st.warning(f"No prediction records available for {selected_ep}.")
        else:
            sample_ids = [r["input"]["sample_id"] for r in ep_records]
            c_sel1, c_sel2 = st.columns([2, 1])
            with c_sel1:
                selected_sample_id = st.selectbox("Select Prediction Sample / Position", sample_ids, index=0)
            with c_sel2:
                render_mode = st.radio("Display Format", ["Interactive Streamlit", "Full HTML Report"], horizontal=True)

            selected_rec = records_by_sample[selected_sample_id]

            if render_mode == "Interactive Streamlit":
                render_prediction_panel_streamlit(selected_rec)
            else:
                html_content = render_prediction_panel_html(selected_rec)
                st.components.v1.html(html_content, height=850, scrolling=True)

    # =======================================================================
    # Tab 5: Tactic Discrepancies
    # =======================================================================
    with tabs[4]:
        st.header("Tactic Mapping Discrepancies")
        st.json(discrepancies)

    # =======================================================================
    # Tab 6: Data Quality & C3
    # =======================================================================
    with tabs[5]:
        st.header("Data Quality & C3 Interface Telemetry")
        st.json(data_quality)

    # =======================================================================
    # Tab 7: Wazuh Telemetry
    # =======================================================================
    with tabs[6]:
        st.header("Raw Wazuh Alert Telemetry")
        if wazuh_alerts_df is not None and not wazuh_alerts_df.empty:
            st.dataframe(wazuh_alerts_df.head(100))
        else:
            st.info("No raw Wazuh alert table loaded.")

    # =======================================================================
    # Tab 8: Export Data
    # =======================================================================
    with tabs[7]:
        st.header("Forensic Artifact Export")
        ep_events = timelines.get(selected_ep, [])
        if ep_events:
            csv_str = export_timeline_to_csv(ep_events)
            json_str = export_timeline_to_json(ep_events)
            st.download_button("Download Timeline CSV", csv_str, f"{selected_ep}_timeline.csv", "text/csv")
            st.download_button("Download Timeline JSON", json_str, f"{selected_ep}_timeline.json", "application/json")


if __name__ == "__main__":
    render_dashboard()
