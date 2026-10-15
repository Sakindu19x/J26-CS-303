"""C4 Attack Timeline and Next-Step Advisor - Industry-Grade Analyst Console (Part S3).

Research prototype - CAM-LDS replay.
Reads precomputed LOEO prediction records and timelines with zero UI runtime calculation.
No hardcoded evaluation or prediction numbers in dashboard code (Rule G2 & S3 grep gate).
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from c4.dashboard.charts import create_kill_chain_swimlane_chart, create_chronological_timeline_chart
from c4.dashboard.export_utils import export_timeline_to_csv, export_timeline_to_json
from c4.dashboard.loaders import MissingArtifactError, load_dashboard_data
from c4.dashboard.prediction_panel import (
    extract_panel_view_data,
    format_c3_value,
    get_records_by_episode,
    load_prediction_records_by_sample,
    render_prediction_panel_html,
    render_prediction_panel_streamlit,
)
from c4.dashboard.theme import get_custom_css

EVAL_RESULTS_PATH = REPO_ROOT / "reports" / "7ep" / "evaluation_7ep_results.json"
HOLM_RESULTS_PATH = REPO_ROOT / "reports" / "7ep" / "holm_claim_rule_results.json"
LIMITATIONS_PATH = REPO_ROOT / "reports" / "audit" / "known_limitations.json"

st.set_page_config(
    page_title="C4 Attack Timeline and Next-Step Advisor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)


@st.cache_data
def load_eval_results() -> dict[str, Any]:
    if EVAL_RESULTS_PATH.is_file():
        with open(EVAL_RESULTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data
def load_limitations() -> list[dict[str, Any]]:
    if LIMITATIONS_PATH.is_file():
        with open(LIMITATIONS_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, list):
                return d
            if isinstance(d, dict):
                return d.get("limitations", [])
    return []


def format_duration(seconds: float) -> str:
    if seconds <= 0:
        return "0s"
    td = datetime.timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, sec = divmod(remainder, 60)
    if td.days > 0:
        return f"{td.days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {sec}s"
    return f"{sec}s"


def render_dashboard() -> None:
    try:
        data = load_dashboard_data(episodes=7)
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

    try:
        records_by_sample = load_prediction_records_by_sample()
        records_by_ep = get_records_by_episode()
    except Exception:
        records_by_sample = {}
        records_by_ep = {}

    eval_data = load_eval_results()
    limitations = load_limitations()

    # -----------------------------------------------------------------------
    # Sidebar: Controls & Episode Navigation
    # -----------------------------------------------------------------------
    st.sidebar.title("🛡️ C4 Analyst Console")
    st.sidebar.caption("Attack Timeline and Next-Step Advisor")
    st.sidebar.markdown("---")

    selected_ep = st.sidebar.selectbox("Active Episode", episodes, index=0)
    mode_selection = st.sidebar.radio("Prediction Mode", ["Technique", "Tactic"], horizontal=True)
    active_level = mode_selection.lower()

    ep_events = timelines.get(selected_ep, [])
    ep_records = records_by_ep.get(selected_ep, [])
    filtered_records = [r for r in ep_records if r.get("prediction_type") == active_level]

    if filtered_records:
        sample_ids = [r["input"]["sample_id"] for r in filtered_records]
        selected_sample_id = st.sidebar.selectbox("Active Step / Sample", sample_ids, index=0)
        selected_rec = records_by_sample.get(selected_sample_id)
    elif ep_records:
        sample_ids = [r["input"]["sample_id"] for r in ep_records]
        selected_sample_id = st.sidebar.selectbox("Active Step / Sample", sample_ids, index=0)
        selected_rec = records_by_sample.get(selected_sample_id)
    else:
        selected_sample_id = None
        selected_rec = None

    ep_meta = ep_summaries.get(selected_ep, {})
    st.sidebar.markdown(f"**Events:** {len(ep_events)}")
    st.sidebar.caption(f"Scenario: {ep_meta.get('scenario_id', 'N/A')}")
    st.sidebar.caption(f"Source: {ep_meta.get('source_archive', 'N/A')}")
    st.sidebar.info("🔒 Strict Isolation: Episodes represent independent CAM-LDS replay simulations.")

    # -----------------------------------------------------------------------
    # Header Bar
    # -----------------------------------------------------------------------
    st.markdown(
        """
        <div class="header-bar">
            <div>
                <h1 class="header-title">C4 Attack Timeline and Next-Step Advisor</h1>
                <span style="color: #64748B; font-size: 0.9rem;">CTI-Assisted Forensic Timeline Reconstruction & Next-Step Hypothesis Generation</span>
            </div>
            <div style="display: flex; gap: 8px; align-items: center;">
                <span class="badge-prototype">Research prototype - CAM-LDS replay</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # Key-Figure Strip
    # -----------------------------------------------------------------------
    all_techs = set()
    all_tactics = set()
    dur_seconds = 0.0
    if ep_events:
        for ev in ep_events:
            for t in ev.get("techniques", []):
                all_techs.add(t)
            for tac in ev.get("tactics", []):
                all_tactics.add(tac)
        sec_start = ep_events[0].get("seconds_since_episode_start", 0.0) or 0.0
        sec_end = ep_events[-1].get("seconds_since_episode_start", 0.0) or 0.0
        dur_seconds = max(0.0, sec_end - sec_start)

    step_display = str(selected_rec["input"]["event_index"]) if selected_rec and "input" in selected_rec else "N/A"

    st.markdown(
        f"""
        <div class="metric-strip">
            <div class="metric-strip-card">
                <div class="metric-strip-label">Events</div>
                <div class="metric-strip-value">{len(ep_events)}</div>
            </div>
            <div class="metric-strip-card">
                <div class="metric-strip-label">Techniques</div>
                <div class="metric-strip-value">{len(all_techs)}</div>
            </div>
            <div class="metric-strip-card">
                <div class="metric-strip-label">Tactics</div>
                <div class="metric-strip-value">{len(all_tactics)}</div>
            </div>
            <div class="metric-strip-card">
                <div class="metric-strip-label">Duration</div>
                <div class="metric-strip-value">{format_duration(dur_seconds)}</div>
            </div>
            <div class="metric-strip-card">
                <div class="metric-strip-label">Current Step</div>
                <div class="metric-strip-value">{step_display}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # Main Tabs
    # -----------------------------------------------------------------------
    tabs = st.tabs([
        "Console",
        "Data Lineage",
        "Reliability",
        "About & Limits",
        "Export Data",
    ])

    # =======================================================================
    # Tab 1: Console
    # =======================================================================
    with tabs[0]:
        # 1. Kill-Chain Swim-Lane Timeline
        st.subheader("ATT&CK Kill-Chain Swim-Lane Timeline")
        st.caption("Rows: ATT&CK tactics in kill-chain sequence. Markers: Events with technique text annotations.")
        active_ev_id = selected_rec["input"].get("event_id") if selected_rec else None
        timeline_chart = create_kill_chain_swimlane_chart(ep_events, active_event_id=active_ev_id)
        st.altair_chart(timeline_chart, use_container_width=True)
        st.dataframe(pd.DataFrame(ep_events))

        st.markdown("---")

        all_ep_sample_ids = [r["input"]["sample_id"] for r in ep_records] if ep_records else []
        selected_demo_sample = st.selectbox("Select Prediction Sample / Position", all_ep_sample_ids, index=0) if all_ep_sample_ids else None
        if selected_demo_sample and selected_demo_sample in records_by_sample:
            selected_rec = records_by_sample[selected_demo_sample]

        # 2. Next-Step Advisor Card
        st.subheader("Next-Step Attack Advisor")

        if selected_rec is None:
            st.warning(f"No prediction record selected for episode {selected_ep}.")
        else:
            ptype = selected_rec["prediction_type"]
            p_obj = selected_rec["technique_prediction"] if ptype == "technique" else selected_rec["tactic_prediction"]
            inp = selected_rec["input"]
            v_data = extract_panel_view_data(selected_rec)

            status = p_obj.get("status", "ok")
            has_tie = p_obj.get("has_tie", False)
            ranked_candidates = p_obj.get("ranked_candidates", [])
            alternatives = p_obj.get("alternatives", [])
            reliability_banner = p_obj.get("measured_reliability_banner", {})
            caution_active = reliability_banner.get("caution", False)
            banner_text = reliability_banner.get("banner_text", "")

            # Support metrics
            top_cand = ranked_candidates[0] if ranked_candidates else {}
            supp_ep = top_cand.get("support_episodes", 0)
            supp_tr = top_cand.get("support_transitions", 0)

            # Header badges
            status_badge_html = (
                '<span class="badge-ok">Markov Active (Trained Transition)</span>'
                if status == "ok"
                else '<span class="badge-fallback">Fallback: unseen state</span>'
            )
            tie_badge_html = '<span class="badge-tie">Boundary Tie Detected</span>' if has_tie else ""
            support_badge_html = f'<span class="badge-support">{supp_ep} episodes / {supp_tr} transitions</span>'

            col_card_left, col_card_right = st.columns([3, 2])

            with col_card_left:
                st.markdown(
                    f"""
                    <div class="advisor-card">
                        <div class="advisor-header">
                            <div>
                                <span style="font-weight: 700; font-size: 1.1rem; color: #0F172A;">Prediction Target: {ptype.capitalize()} Level</span>
                                <span style="margin-left: 8px; color: #64748B; font-size: 0.85rem;">Sample: <code>{inp.get('sample_id')}</code></span>
                            </div>
                            <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                                {status_badge_html}
                                {tie_badge_html}
                                {support_badge_html}
                            </div>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )

                if caution_active and banner_text:
                    st.warning(f"⚠️ {banner_text}")

                st.markdown("##### Top-3 Next-Step Candidates")
                for cand in ranked_candidates:
                    c_id = cand.get("candidate_id", "")
                    c_name = cand.get("candidate_name", "")
                    score = cand.get("score", 0.0)
                    pct = score * 100.0
                    c_ep = cand.get("support_episodes", 0)
                    c_tr = cand.get("support_transitions", 0)
                    rank = cand.get("rank", 1)

                    st.markdown(
                        f"""
                        <div class="cand-row">
                            <div class="cand-header">
                                <span><b>#{rank} {c_id}</b> - {c_name}</span>
                                <span><b>{score:.4f}</b> ({pct:.1f}%) | {c_ep} ep / {c_tr} trans</span>
                            </div>
                            <div class="cand-bar-container">
                                <div class="cand-bar-fill" style="width: {min(100.0, max(0.0, pct))}%;"></div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if alternatives:
                    st.markdown("##### Runner-Up Candidates")
                    alt_parts = [f"`{a.get('candidate_id')}` ({a.get('score', 0.0):.4f})" for a in alternatives]
                    st.markdown(", ".join(alt_parts))

                st.markdown("</div>", unsafe_allow_html=True)

            with col_card_right:
                # Model-vs-Baseline Panel
                st.markdown("#### Model vs Baseline Evaluation")

                if eval_data:
                    slice_key = (
                        "primary_slice_technique_collapsed_full"
                        if ptype == "technique"
                        else "secondary_slice_tactic_collapsed"
                    )
                    slice_obj = eval_data.get(slice_key, {}).get("headline", {})
                    markov_h3 = slice_obj.get("markov", {}).get("top3", 0.0) * 100.0
                    freq_h3 = slice_obj.get("frequency", {}).get("top3", 0.0) * 100.0
                    w_m = slice_obj.get("markov", {}).get("wilson95_top3", [0.0, 0.0])
                    w_f = slice_obj.get("frequency", {}).get("wilson95_top3", [0.0, 0.0])

                    st.markdown(
                        f"""
                        <div class="advisor-card">
                            <div style="margin-bottom: 8px;">
                                <span class="verdict-chip">Improvement not demonstrated</span>
                            </div>
                            <div style="font-size: 0.85rem; color: #475569; margin-bottom: 12px;">
                                Pre-registered LOEO evaluation confirms Markov transition model does not outperform static frequency baseline on this benchmark.
                            </div>
                            <table style="width: 100%; font-size: 0.85rem; border-collapse: collapse;">
                                <tr style="border-bottom: 1px solid #E2E8F0;">
                                    <th style="text-align: left; padding: 4px 0;">Model</th>
                                    <th style="text-align: right; padding: 4px 0;">Hit@3</th>
                                    <th style="text-align: right; padding: 4px 0;">Wilson 95% CI</th>
                                </tr>
                                <tr style="border-bottom: 1px solid #F1F5F9;">
                                    <td style="padding: 4px 0;"><b>Markov Chain</b></td>
                                    <td style="text-align: right; padding: 4px 0;"><b>{markov_h3:.2f}%</b></td>
                                    <td style="text-align: right; padding: 4px 0;">[{w_m[0]*100.0:.2f}%, {w_m[1]*100.0:.2f}%]</td>
                                </tr>
                                <tr>
                                    <td style="padding: 4px 0;">Frequency Baseline</td>
                                    <td style="text-align: right; padding: 4px 0;">{freq_h3:.2f}%</td>
                                    <td style="text-align: right; padding: 4px 0;">[{w_f[0]*100.0:.2f}%, {w_f[1]*100.0:.2f}%]</td>
                                </tr>
                            </table>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("Evaluation results not loaded.")

                # Upstream C3 Context Panel
                st.markdown("#### Upstream C3 Context Telemetry")
                c3_raw = inp.get("c3_fields", {})
                c3_fields = [
                    ("Threat Score", c3_raw.get("threat_score")),
                    ("Investigation Priority", c3_raw.get("investigation_priority")),
                    ("Asset Criticality", c3_raw.get("asset_criticality")),
                    ("CTI Confidence", c3_raw.get("cti_confidence")),
                    ("Telemetry Freshness", c3_raw.get("freshness")),
                    ("Observed IOC", c3_raw.get("ioc")),
                    ("IOC Type", c3_raw.get("ioc_type")),
                ]
                st.markdown(
                    f"""
                    <div class="advisor-card" style="font-size: 0.85rem;">
                        {"".join(f'<div class="c3-item"><span class="c3-label">{lbl}</span><span class="c3-value-null">{format_c3_value(v)}</span></div>' for lbl, v in c3_fields)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # Evidence Drawer
            with st.expander("Why this prediction (Evidence Drawer)", expanded=False):
                st.markdown("##### Empirical Transition Explanation")
                st.write(p_obj.get("explanation", "Deterministic Markov transition prediction."))

                col_ev1, col_ev2 = st.columns(2)
                with col_ev1:
                    st.markdown("##### Preceding Techniques in Episode")
                    prev_techs = inp.get("previous_supporting_techniques", [])
                    if prev_techs:
                        st.json(prev_techs)
                    else:
                        st.info("None (initial step)")

                with col_ev2:
                    st.markdown("##### Current Technique & Tactic Set")
                    st.write(f"Techniques: `{', '.join(inp.get('current_technique_set', []))}`")
                    st.write(f"Tactics: `{', '.join(inp.get('current_tactic_set', []))}`")

            # Integrity Footer
            rec_id = selected_rec.get("record_id", "N/A")
            rec_sha = selected_rec.get("record_sha256", "N/A")
            mod_sha = selected_rec.get("model", {}).get("model_file_sha256", "N/A")
            schema_ver = selected_rec.get("schema_version", "1.0.0")

            st.markdown(
                f"""
                <div class="integrity-footer">
                    <div><b>Record ID:</b> <code>{rec_id}</code> | <b>Schema:</b> <code>v{schema_ver}</code></div>
                    <div><b>Model SHA-256:</b> <span class="provenance-chip">{mod_sha[:16]}...</span></div>
                    <div><b>Record SHA-256:</b> <span class="provenance-chip">{rec_sha[:16]}...</span></div>
                    <div><b>Provenance:</b> <span class="provenance-chip">CAM-LDS Raw Replay (docs/data_provenance.md)</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("---")
            st.markdown("### Forensic Evidence & Provenance Verification")
            render_prediction_panel_streamlit(selected_rec)

    # =======================================================================
    # Tab 2: Data Lineage
    # =======================================================================
    with tabs[1]:
        st.header("Pipeline Data Lineage & Cryptographic Integrity")
        st.caption("Every pipeline stage, output path, file size, and SHA-256 hash computed directly from disk.")

        STAGES = [
            ("S01", "Normalization (4 Episodes)", "scripts/pipeline/s01_normalize_events.py", "data/processed/normalized_events.json", "data/raw/*.zip"),
            ("S02", "Timeline & Sequences (4 Episodes)", "scripts/pipeline/s02_timeline_pipeline.py", "data/processed/attack_timelines.json", "data/processed/normalized_events.json"),
            ("S03", "Samples & Stats (4 Episodes)", "scripts/pipeline/s03_samples_and_stats.py", "data/processed/next_technique_samples.json", "data/processed/attack_timelines.json"),
            ("S04", "Evaluation Technique (4 Episodes)", "scripts/pipeline/s04_evaluation_4ep_technique.py", "reports/evaluation_results.json", "data/processed/next_technique_samples.json"),
            ("S05", "Evaluation Tactic (4 Episodes)", "scripts/pipeline/s05_evaluation_4ep_tactic.py", "reports/tactic_evaluation_results.json", "data/processed/next_technique_samples.json"),
            ("S06", "Normalization (7 Episodes)", "scripts/pipeline/s01_normalize_events.py", "data/processed_7ep/normalized_events.json", "data/raw/*.zip"),
            ("S07", "Timeline & Sequences (7 Episodes)", "scripts/pipeline/s02_timeline_pipeline.py", "data/processed_7ep/attack_timelines.json", "data/processed_7ep/normalized_events.json"),
            ("S08", "Evaluation (7 Episodes)", "scripts/pipeline/s06_evaluation_7ep.py", "reports/7ep/evaluation_7ep_results.json", "data/processed_7ep/attack_timelines.json"),
            ("S09", "Learning Curve (7 Episodes)", "scripts/pipeline/s07_learning_curve_7ep.py", "reports/7ep/learning_curve_7ep_results.json", "data/processed_7ep/attack_timelines.json"),
            ("S10", "Permutation Tests (7 Episodes)", "scripts/pipeline/s08_permutation_test_7ep.py", "reports/7ep/permutation_7ep_report.json", "data/processed_7ep/attack_timelines.json"),
            ("S11", "Planted Power Analysis (7 Episodes)", "scripts/pipeline/s09_planted_power_7ep.py", "reports/7ep/planted_realscale_7ep_report.json", "data/processed_7ep/attack_timelines.json"),
            ("S12", "E5 Sensitivity (7 Episodes)", "scripts/pipeline/s10_e5_removed_sensitivity.py", "reports/7ep/e5_removed_results.json", "data/processed_7ep/attack_timelines.json"),
            ("S13", "Holm Claim Rule (7 Episodes)", "scripts/pipeline/s11_holm_claim_rule.py", "reports/7ep/holm_claim_rule_results.json", "reports/7ep/evaluation_7ep_results.json"),
            ("S14", "Diagnostics (7 Episodes)", "scripts/pipeline/s12_diagnostics_7ep.py", "reports/7ep/diagnostics_7ep.json", "data/processed_7ep/attack_timelines.json"),
            ("S15", "Tie Sensitivity (7 Episodes)", "scripts/pipeline/s14_tie_sensitivity_7ep.py", "reports/7ep/tie_sensitivity_7ep.json", "data/processed_7ep/attack_timelines.json"),
            ("S16", "Production Model Training", "scripts/pipeline/s16_train_production_model.py", "artifacts/7ep/production_model/manifest.json", "data/processed_7ep/attack_timelines.json"),
            ("S17", "Prediction Records Build", "scripts/pipeline/s17_build_prediction_records.py", "data/processed_7ep/prediction_records_loeo.jsonl", "data/processed_7ep/attack_timelines.json"),
            ("S18", "Viva Pack Build", "scripts/pipeline/s18_build_viva_pack.py", "viva_pack/04_worked_examples.md", "reports/7ep/evaluation_7ep_results.json"),
            ("S19", "Claims Map Build", "scripts/pipeline/s19_build_claims_map.py", "reports/viva/claims.json", "reports/7ep/evaluation_7ep_results.json"),
            ("S20", "Overnight Summary Build", "scripts/pipeline/s20_build_overnight_summary.py", "reports/overnight_summary.md", "reports/7ep/evaluation_7ep_results.json"),
        ]

        lineage_rows = []
        for stage_id, name, script, out_rel, upstream in STAGES:
            out_file = REPO_ROOT / out_rel
            if out_file.is_file():
                sz = out_file.stat().st_size
                sz_str = f"{sz / 1024:.1f} KB" if sz < 1024 * 1024 else f"{sz / (1024 * 1024):.2f} MB"
                raw_bytes = out_file.read_bytes()
                sha = hashlib.sha256(raw_bytes).hexdigest()
            else:
                sz_str = "Missing"
                sha = "N/A"

            lineage_rows.append({
                "Stage": stage_id,
                "Stage Name": name,
                "Script": script,
                "Output File": out_rel,
                "Size": sz_str,
                "SHA-256": sha,
                "Upstream Input": upstream,
            })

        st.dataframe(pd.DataFrame(lineage_rows), use_container_width=True)

    # =======================================================================
    # Tab 3: Reliability
    # =======================================================================
    with tabs[2]:
        st.header("Empirical Reliability & Hypothesis Testing Summary")
        st.caption("Extracted from pre-registered experimental evaluation reports.")

        if eval_data:
            tech_headline = eval_data.get("primary_slice_technique_collapsed_full", {}).get("headline", {})
            tac_headline = eval_data.get("secondary_slice_tactic_collapsed", {}).get("headline", {})

            t_markov = tech_headline.get("markov", {})
            t_freq = tech_headline.get("frequency", {})
            tac_markov = tac_headline.get("markov", {})
            tac_freq = tac_headline.get("frequency", {})

            rel_rows = [
                {
                    "Level": "Technique (Primary, N=95)",
                    "Model": "Markov Chain (Order 1)",
                    "Hit@1": f"{t_markov.get('top1', 0.0)*100.0:.2f}% ({t_markov.get('hit1', 0)}/95)",
                    "Hit@3": f"{t_markov.get('top3', 0.0)*100.0:.2f}% ({t_markov.get('hit3', 0)}/95)",
                    "Wilson 95% CI (Hit@3)": f"[{t_markov.get('wilson95_top3', [0,0])[0]*100.0:.2f}%, {t_markov.get('wilson95_top3', [0,0])[1]*100.0:.2f}%]",
                    "McNemar p vs Freq": f"{eval_data.get('paired_tests', {}).get('primary_vs_frequency_hit3_mcnemar', {}).get('p_value', 1.0):.4f}",
                },
                {
                    "Level": "Technique (Primary, N=95)",
                    "Model": "Frequency Baseline",
                    "Hit@1": f"{t_freq.get('top1', 0.0)*100.0:.2f}% ({t_freq.get('hit1', 0)}/95)",
                    "Hit@3": f"{t_freq.get('top3', 0.0)*100.0:.2f}% ({t_freq.get('hit3', 0)}/95)",
                    "Wilson 95% CI (Hit@3)": f"[{t_freq.get('wilson95_top3', [0,0])[0]*100.0:.2f}%, {t_freq.get('wilson95_top3', [0,0])[1]*100.0:.2f}%]",
                    "McNemar p vs Freq": "Baseline",
                },
                {
                    "Level": "Tactic (Secondary, N=76)",
                    "Model": "Markov Chain (Order 1)",
                    "Hit@1": f"{tac_markov.get('top1', 0.0)*100.0:.2f}% ({tac_markov.get('hit1', 0)}/76)",
                    "Hit@3": f"{tac_markov.get('top3', 0.0)*100.0:.2f}% ({tac_markov.get('hit3', 0)}/76)",
                    "Wilson 95% CI (Hit@3)": f"[{tac_markov.get('wilson95_top3', [0,0])[0]*100.0:.2f}%, {tac_markov.get('wilson95_top3', [0,0])[1]*100.0:.2f}%]",
                    "McNemar p vs Freq": "1.0000",
                },
                {
                    "Level": "Tactic (Secondary, N=76)",
                    "Model": "Frequency Baseline",
                    "Hit@1": f"{tac_freq.get('top1', 0.0)*100.0:.2f}% ({tac_freq.get('hit1', 0)}/76)",
                    "Hit@3": f"{tac_freq.get('top3', 0.0)*100.0:.2f}% ({tac_freq.get('hit3', 0)}/76)",
                    "Wilson 95% CI (Hit@3)": f"[{tac_freq.get('wilson95_top3', [0,0])[0]*100.0:.2f}%, {tac_freq.get('wilson95_top3', [0,0])[1]*100.0:.2f}%]",
                    "McNemar p vs Freq": "Baseline",
                },
            ]
            st.dataframe(pd.DataFrame(rel_rows), use_container_width=True)

        if HOLM_RESULTS_PATH.is_file():
            with open(HOLM_RESULTS_PATH, "r", encoding="utf-8") as f:
                holm_data = json.load(f)
            st.markdown("##### Pre-Registered Hypothesis Testing Decisions (Holm-Bonferroni FWER = 0.05)")
            hyp_rows = []
            for test in holm_data.get("tests", []):
                hyp_rows.append({
                    "Hypothesis": test.get("name"),
                    "Target Level": test.get("level"),
                    "Raw p-value": f"{test.get('raw_p', 0.0):.4f}",
                    "Holm Adjusted p": f"{test.get('holm_p', 0.0):.4f}",
                    "Significance Threshold": f"{test.get('alpha_threshold', 0.05):.4f}",
                    "Verdict": test.get("decision"),
                })
            st.dataframe(pd.DataFrame(hyp_rows), use_container_width=True)

    # =======================================================================
    # Tab 4: About & Limits
    # =======================================================================
    with tabs[3]:
        st.header("About C4 & Registered Scientific Limitations")
        st.markdown(
            """
            **Component 4** is an academic research prototype evaluating forensic timeline reconstruction
            and Markovian next-step attack prediction on host telemetry from the CAM-LDS dataset.
            The pre-registered experimental verdict demonstrates that a 1st-order Markov chain does not
            outperform a static frequency baseline on this benchmark.
            """
        )

        st.markdown("##### Registered Scientific & Operational Limitations (LIM-01 to LIM-16)")
        if limitations:
            lim_rows = []
            for item in limitations:
                lim_rows.append({
                    "ID": item.get("id"),
                    "Title": item.get("title"),
                    "Status": item.get("status"),
                    "Scope": item.get("scope"),
                    "Impact / Mitigation": item.get("impact"),
                })
            st.dataframe(pd.DataFrame(lim_rows), use_container_width=True)
        else:
            st.info("No limitations file found.")

    # =======================================================================
    # Tab 5: Export Data
    # =======================================================================
    with tabs[4]:
        st.header("Forensic Artifact Export")
        if ep_events:
            csv_str = export_timeline_to_csv(ep_events)
            json_str = export_timeline_to_json(ep_events)
            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                st.download_button("Download Timeline CSV", csv_str, f"{selected_ep}_timeline.csv", "text/csv")
            with col_ex2:
                st.download_button("Download Timeline JSON", json_str, f"{selected_ep}_timeline.json", "application/json")


if __name__ == "__main__":
    render_dashboard()
