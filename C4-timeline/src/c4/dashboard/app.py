"""C4 Digital Forensic Investigation Prototype - Streamlit Dashboard."""
from __future__ import annotations

import json
import sys
from datetime import datetime
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
from c4.timeline import C3_FIELDS, filter_timeline

# ---------------------------------------------------------------------------
# Streamlit Page Config & Styling
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="C4 Forensic Timeline & Attack Sequences",
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
    .causality-box {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        padding: 12px;
        border-radius: 4px;
        margin-bottom: 16px;
        font-size: 0.95rem;
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

    # -----------------------------------------------------------------------
    # Sidebar: Episode Selector & Run Metadata
    # -----------------------------------------------------------------------
    st.sidebar.title("🛡️ C4 Forensic Prototype")
    st.sidebar.caption("CTI-Assisted Forensic Timeline Reconstruction")

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
        "4. Tactic Discrepancies",
        "5. Data Quality & C3",
        "6. Wazuh Telemetry",
        "7. Export Data",
    ])

    # =======================================================================
    # Tab 1: Overview
    # =======================================================================
    with tabs[0]:
        st.header("Campaign Overview & Telemetry Summary")

        dq_summary = data_quality.get("summary", {})
        total_events = dq_summary.get("total_events", sum(len(t) for t in timelines.values()))
        total_labeled = dq_summary.get("total_labeled", 0)
        labeled_pct = (total_labeled / total_events * 100) if total_events > 0 else 0.0

        all_techniques = set()
        for ep_rows in timelines.values():
            for r in ep_rows:
                for t in r.get("techniques", []):
                    if t:
                        all_techniques.add(t)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Campaign Episodes", len(episodes))
        col2.metric("Total Events", total_events)
        col3.metric("Labeled Events", f"{total_labeled} ({labeled_pct:.1f}%)")
        col4.metric("Distinct Techniques", len(all_techniques))
        col5.metric("Tactic Discrepancies", discrepancies.get("discrepancies_count", 0))

        st.subheader("Episode Campaign Comparison")
        comp_rows = []
        for ep_id in episodes:
            s = ep_summaries.get(ep_id, {})
            seq_info = sequences.get("episodes", {}).get(ep_id, {})
            comp_rows.append({
                "Episode": ep_id,
                "Scenario ID": s.get("scenario_id"),
                "Source Archive": s.get("source_archive"),
                "Total Events": s.get("total_events", len(timelines.get(ep_id, []))),
                "Labeled (Ground Truth)": s.get("labeled_events", 0),
                "Unlabeled": s.get("unlabeled_events", 0),
                "Raw Sequence Length": seq_info.get("raw_length", 0),
                "Collapsed Sequence Length": seq_info.get("collapsed_length", 0),
                "Distinct Techniques": seq_info.get("distinct_techniques_count", 0),
            })
        st.dataframe(pd.DataFrame(comp_rows), use_container_width=True)

    # =======================================================================
    # Tab 2: Episode Timeline
    # =======================================================================
    with tabs[1]:
        st.header(f"Chronological Timeline — Episode {selected_ep}")

        ep_events = timelines.get(selected_ep, [])

        # Filters Section
        with st.expander("🔍 Filter Controls", expanded=True):
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)

            # Extract distinct values for dropdowns
            hostnames = sorted(list({e.get("hostname") for e in ep_events if e.get("hostname")}))
            all_techs_ep = sorted(list({t for e in ep_events for t in e.get("techniques", [])}))
            all_tacs_ep = sorted(list({t for e in ep_events for t in e.get("tactics", [])}))

            selected_host = f_col1.selectbox("Hostname", ["(All)"] + hostnames)
            selected_tech = f_col2.selectbox("Technique", ["(All)"] + all_techs_ep)
            selected_tac = f_col3.selectbox("Dataset Tactic", ["(All)"] + all_tacs_ep)
            selected_status = f_col4.selectbox("Label Status", ["(All)", "ground_truth", "unlabeled"])

            chart_y_mode = st.radio("Y-Axis Mode", ["Step Execution Order", "Primary Technique"], horizontal=True)

        # Apply Filters using processing module filter_timeline
        filtered_events = filter_timeline(
            events=ep_events,
            episode_id=selected_ep,
            hostname=None if selected_host == "(All)" else selected_host,
            technique=None if selected_tech == "(All)" else selected_tech,
            tactic=None if selected_tac == "(All)" else selected_tac,
            label_status=None if selected_status == "(All)" else selected_status,
        )

        st.caption(f"Showing **{len(filtered_events)}** of **{len(ep_events)}** events in Episode {selected_ep}")

        # Render Plotly Chart
        y_mode = "technique" if chart_y_mode == "Primary Technique" else "step_index"
        fig = create_chronological_timeline_chart(filtered_events, y_axis_mode=y_mode)
        st.plotly_chart(fig, use_container_width=True)

        # Tabular View of Filtered Events
        if filtered_events:
            table_records = []
            for ev in filtered_events:
                table_records.append({
                    "Event ID": ev["event_id"],
                    "Timestamp (UTC)": ev["timestamp"],
                    "Status": ev["label_status"],
                    "Step Type": ev.get("step_type"),
                    "Command": (ev.get("cmd") or "")[:45],
                    "Hostname": ev.get("hostname"),
                    "Techniques": ", ".join(ev.get("techniques", [])),
                    "Dataset Tactics": ", ".join(ev.get("tactics", [])),
                })
            st.dataframe(pd.DataFrame(table_records), use_container_width=True, height=240)

            # Single Event Details Inspector
            st.subheader("Event Detail Inspector")
            event_id_list = [e["event_id"] for e in filtered_events]
            inspected_id = st.selectbox("Select Event ID to inspect", event_id_list)
            inspected_ev = next(e for e in filtered_events if e["event_id"] == inspected_id)

            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.markdown(f"**Event ID:** <code>{inspected_ev['event_id']}</code>", unsafe_allow_html=True)
                st.markdown(f"**Episode ID:** <code>{inspected_ev['episode_id']}</code>", unsafe_allow_html=True)
                st.markdown(f"**Timestamp (UTC):** <code>{inspected_ev['timestamp']}</code>", unsafe_allow_html=True)
                st.markdown(f"**Step Type:** <code>{inspected_ev.get('step_type')}</code>", unsafe_allow_html=True)
                st.markdown(f"**Command:** <code>{inspected_ev.get('cmd')}</code>", unsafe_allow_html=True)
                st.markdown(f"**Hostname:** <code>{inspected_ev.get('hostname')}</code>", unsafe_allow_html=True)
                st.markdown(f"**Username:** <code>{inspected_ev.get('username')}</code>", unsafe_allow_html=True)

            with d_col2:
                # Techniques & Tactics with clear badges
                tech_list = inspected_ev.get("techniques", [])
                st.markdown(f"**Techniques:** <span class='badge-gt'>GROUND TRUTH</span> {', '.join(tech_list) if tech_list else 'None'}", unsafe_allow_html=True)

                ds_tactics = inspected_ev.get("tactics", [])
                st.markdown(f"**Dataset Tactics:** <span class='badge-gt'>GROUND TRUTH</span> {', '.join(ds_tactics) if ds_tactics else 'None'}", unsafe_allow_html=True)

                off_tactics = inspected_ev.get("official_tactics", [])
                st.markdown(f"**Official Tactics:** <span class='badge-derived'>DERIVED (ATT&CK v16.1)</span> {', '.join(off_tactics) if off_tactics else 'None'}", unsafe_allow_html=True)

                loc_occ = inspected_ev.get("local_occurrence")
                st.markdown(f"**Local Occurrence:** <span class='badge-derived'>DERIVED</span> <code>{json.dumps(loc_occ) if loc_occ else 'None'}</code>", unsafe_allow_html=True)

                # C3 Fields
                st.markdown("---")
                st.markdown("<b>C3 Component Fields:</b>", unsafe_allow_html=True)
                c3_sub = []
                for f_name in C3_FIELDS:
                    val = inspected_ev.get(f_name)
                    c3_sub.append(f"• <code>{f_name}</code>: <span class='badge-missing'>MISSING</span>" if val is None else f"• <code>{f_name}</code>: {val}")
                st.markdown("<br>".join(c3_sub), unsafe_allow_html=True)
        else:
            st.warning("No events match the selected filter criteria.")

    # =======================================================================
    # Tab 3: ATT&CK Sequences
    # =======================================================================
    with tabs[2]:
        st.header(f"ATT&CK Manifestation Sequence — Episode {selected_ep}")

        st.markdown(
            """
            <div class="causality-box">
                <b>⚠️ Forensic Causality Notice:</b> Chronological ordering of attack steps reflects the temporal
                manifestation sequence recorded in telemetry; temporal precedence does not by itself prove causal dependency.
            </div>
            """,
            unsafe_allow_html=True,
        )

        ep_seq_dict = sequences.get("episodes", {}).get(selected_ep, {})
        seq_variant = st.radio("Sequence Variant", ["Collapsed (Merged consecutive identical technique sets)", "Raw (All labeled steps)"], horizontal=True)

        variant_key = "collapsed" if "Collapsed" in seq_variant else "raw"
        items = ep_seq_dict.get(variant_key, [])

        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Sequence Length", len(items))
        m_col2.metric("Raw Steps", ep_seq_dict.get("raw_length", 0))
        m_col3.metric("Collapsed Steps", ep_seq_dict.get("collapsed_length", 0))

        st.subheader("Ordered Sequence Steps")
        seq_table = []
        for idx, it in enumerate(items, 1):
            if variant_key == "collapsed":
                seq_table.append({
                    "Step": idx,
                    "Repeat Count": it.get("repeat_count", 1),
                    "Merged Event IDs": ", ".join(it.get("event_ids", [])),
                    "Start Time (UTC)": it.get("timestamp"),
                    "End Time (UTC)": it.get("end_timestamp"),
                    "Technique Set": ", ".join(it.get("techniques", [])),
                    "Dataset Tactics": ", ".join(it.get("tactics", [])),
                    "Official Tactics": ", ".join(it.get("official_tactics", [])),
                    "Skipped Before": it.get("unlabeled_steps_skipped_before", 0),
                    "Skipped Between": str(it.get("unlabeled_steps_skipped_between", [])),
                })
            else:
                seq_table.append({
                    "Step": idx,
                    "Event ID": it.get("event_id"),
                    "Timestamp (UTC)": it.get("timestamp"),
                    "Technique Set": ", ".join(it.get("techniques", [])),
                    "Dataset Tactics": ", ".join(it.get("tactics", [])),
                    "Official Tactics": ", ".join(it.get("official_tactics", [])),
                    "Skipped Before": it.get("unlabeled_steps_skipped_before", 0),
                })
        st.dataframe(pd.DataFrame(seq_table), use_container_width=True)

    # =======================================================================
    # Tab 4: Tactic Discrepancy Panel
    # =======================================================================
    with tabs[3]:
        st.header("ATT&CK Tactic Discrepancy Analysis")

        st.markdown(
            """
            This panel identifies cases where the step-level tactic assigned in the CAM-LDS ground-truth dataset
            differs from the official MITRE ATT&CK Enterprise v16.1 tactic definitions for that technique.
            """
        )

        disc_list = discrepancies.get("discrepancies", [])
        st.info(f"Total Discrepancies across all episodes: **{len(disc_list)}** events.")

        disc_df = pd.DataFrame([
            {
                "Event ID": d["event_id"],
                "Episode": d["episode_id"],
                "Technique(s)": ", ".join(d["techniques"]),
                "Dataset Tactics (Labeled)": ", ".join(d["dataset_tactics"]),
                "Official ATT&CK Tactics": ", ".join(d["official_tactics"]),
                "Discrepant Tactic(s)": ", ".join(d["discrepancy_tactics"]),
            }
            for d in disc_list
        ])
        st.dataframe(disc_df, use_container_width=True)

    # =======================================================================
    # Tab 5: Data Quality & C3 Provenance
    # =======================================================================
    with tabs[4]:
        st.header("Data Quality Assurance & Field Provenance")

        q_issues = data_quality.get("quality_issues", {})
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Parsing Errors", len(data_quality.get("skipped_records", [])))
        col2.metric("Whitespace Fixes", q_issues.get("whitespace_fixes_count", 0))
        col3.metric("Malformed Keys Recovered", q_issues.get("malformed_records_count", 0))
        col4.metric("Missing Timestamps", q_issues.get("missing_timestamps_count", 0))

        if q_issues.get("whitespace_fixes"):
            st.subheader("Whitespace Cleaning Log")
            st.dataframe(pd.DataFrame(q_issues["whitespace_fixes"]), use_container_width=True)

        st.subheader("Field Provenance Table (C3 Integration Plan)")
        st.dataframe(pd.DataFrame(data_quality.get("field_provenance_table", [])), use_container_width=True)

    # =======================================================================
    # Tab 6: Wazuh Telemetry (Detector Output)
    # =======================================================================
    with tabs[5]:
        st.header(f"Wazuh Host Telemetry — Episode {selected_ep}")

        st.caption("ℹ️ **Notice:** Wazuh alerts are detector-derived outputs, not ground-truth labels. They are not linked to individual attack steps.")

        w_summary = data_quality.get("wazuh_alerts", {}).get(selected_ep, {})
        w1, w2, w3, w4 = st.columns(4)
        w1.metric("Total Archive Alerts", w_summary.get("total_alerts", 0))
        w2.metric("In Attack Window", w_summary.get("in_window", 0))
        w3.metric("Before Window", w_summary.get("excluded_before_window", 0))
        w4.metric("After Window", w_summary.get("excluded_after_window", 0))

        top_rules = w_summary.get("top_10_rules", [])
        if top_rules:
            st.subheader("Top Rules in Attack Window by (rule.id, description)")
            st.dataframe(pd.DataFrame(top_rules), use_container_width=True)

    # =======================================================================
    # Tab 7: Export Data
    # =======================================================================
    with tabs[6]:
        st.header(f"Export Reconstructed Timeline — Episode {selected_ep}")

        st.markdown(
            f"""
            Export the complete reconstructed timeline for **Episode {selected_ep}** ({len(ep_events)} events).
            Both formats strictly preserve <code>episode_id</code>, <code>event_id</code>, and chronological metadata.
            """,
            unsafe_allow_html=True,
        )

        csv_data = export_timeline_to_csv(ep_events)
        json_data = export_timeline_to_json(ep_events)

        c1, c2 = st.columns(2)
        c1.download_button(
            label=f"⬇️ Download {selected_ep} Timeline (CSV)",
            data=csv_data,
            file_name=f"attack_timeline_{selected_ep}.csv",
            mime="text/csv",
        )
        c2.download_button(
            label=f"⬇️ Download {selected_ep} Timeline (JSON)",
            data=json_data,
            file_name=f"attack_timeline_{selected_ep}.json",
            mime="application/json",
        )


if __name__ == "__main__":
    render_dashboard()
