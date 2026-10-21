"""Next-Step Prediction Dashboard Panel (FR6, FR7, FR9, NFR4, NFR6).

Provides deterministic data extraction and HTML/Streamlit rendering for
Component 4 explainable prediction records in demo mode without performing
any runtime computation in the UI.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
JSONL_PATH = REPO_ROOT / "data" / "processed_7ep" / "prediction_records_loeo.jsonl"


def load_prediction_records_by_sample() -> dict[str, dict[str, Any]]:
    """Load all 171 LOEO prediction records indexed by sample_id."""
    records_map: dict[str, dict[str, Any]] = {}
    if not JSONL_PATH.is_file():
        raise FileNotFoundError(f"Missing prediction records JSONL: {JSONL_PATH}")
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                sid = rec["input"]["sample_id"]
                records_map[sid] = rec
    return records_map


def format_c3_value(val: Any) -> str:
    """Format C3 field value; display 'not provided by dataset' when null."""
    if val is None or val == "":
        return "not provided by dataset"
    return str(val)


def extract_panel_view_data(record: dict[str, Any]) -> dict[str, Any]:
    """Extract display data directly from record fields without UI computation."""
    inp = record["input"]
    pred_level = record["prediction_type"]
    p_obj = record["technique_prediction"] if pred_level == "technique" else record["tactic_prediction"]
    assert p_obj is not None, "Missing prediction object in record"

    c3_raw = inp.get("c3_fields", {})
    c3_display = {
        "threat_score": format_c3_value(c3_raw.get("threat_score")),
        "investigation_priority": format_c3_value(c3_raw.get("investigation_priority")),
        "asset_criticality": format_c3_value(c3_raw.get("asset_criticality")),
        "cti_confidence": format_c3_value(c3_raw.get("cti_confidence")),
        "freshness": format_c3_value(c3_raw.get("freshness")),
        "ioc": format_c3_value(c3_raw.get("ioc")),
        "ioc_type": format_c3_value(c3_raw.get("ioc_type")),
    }

    status = p_obj["status"]
    status_badge = {
        "ok": ("Markov Active (Trained Transition)", "badge-success"),
        "fallback": ("Frequency Fallback (Unseen State)", "badge-warning"),
        "unseen_state": ("Unseen State", "badge-danger"),
    }.get(status, (status, "badge-secondary"))

    tie_flags = p_obj.get("tie_flags", {})
    if tie_flags.get("tie_at_top1"):
        tie_notice = f"Notice: Top-1 rank boundary is tied between candidates: {', '.join(tie_flags.get('tied_candidates', []))} (broken by lexicographical order)"
    elif tie_flags.get("tie_at_top3_boundary"):
        tie_notice = f"Notice: Top-3 rank boundary is tied with alternative candidates: {', '.join(tie_flags.get('tied_candidates', []))} (broken by lexicographical order)"
    else:
        tie_notice = "No boundary ties detected."

    return {
        "sample_id": inp["sample_id"],
        "episode_id": inp["episode_id"],
        "prediction_level": pred_level,
        "event_index": inp.get("event_index"),
        "last_timestamp": inp.get("last_timestamp"),
        "current_techniques": inp.get("current_technique_set", []),
        "current_tactics": inp.get("current_tactic_set", []),
        "previous_supporting_techniques": inp.get("previous_supporting_techniques", []),
        "incident_stage": format_c3_value(inp.get("incident_stage")),
        "affected_asset": format_c3_value(inp.get("affected_asset")),
        "c3_fields": c3_display,
        "status": status,
        "status_badge_text": status_badge[0],
        "status_badge_class": status_badge[1],
        "ranked_candidates": p_obj.get("ranked_candidates", []),
        "alternatives": p_obj.get("alternatives", []),
        "tie_notice": tie_notice,
        "reliability_banner": p_obj.get("measured_reliability_banner", {}).get("banner_text", ""),
        "explanation": p_obj.get("explanation", ""),
        "support": p_obj.get("support", {}),
        "caution": p_obj.get("support", {}).get("caution", False),
        "caution_text": p_obj.get("support", {}).get("caution_text"),
        "record_id": record["record_id"],
        "model_file_sha256": record["model"]["model_file_sha256"],
        "input_events_sha256": record["input_events_sha256"],
        "record_sha256": record["record_sha256"],
    }


def render_prediction_panel_html(record: dict[str, Any]) -> str:
    """Generate standalone HTML document rendering the Next-Step Prediction panel."""
    d = extract_panel_view_data(record)

    cand_rows = []
    for idx, c in enumerate(d["ranked_candidates"], start=1):
        ep_ids = ", ".join(c.get("supporting_episode_ids", [])) if c.get("supporting_episode_ids") else "none"
        t_disp = ", ".join(c.get("tactic_display", [])) if c.get("tactic_display") else ", ".join(c.get("tactics", []))
        cand_rows.append(
            f"<tr>"
            f"<td><b>{idx}</b></td>"
            f"<td><code>{c['candidate_id']}</code></td>"
            f"<td>{c.get('candidate_name') or 'N/A'}</td>"
            f"<td><b>{c['score']:.4f}</b></td>"
            f"<td><code>{c['score_type']}</code></td>"
            f"<td>{c['numerator']:.2f} / {c['denominator']:.2f}</td>"
            f"<td>[{ep_ids}]</td>"
            f"<td>{t_disp}</td>"
            f"</tr>"
        )

    alt_rows = []
    for idx, a in enumerate(d["alternatives"], start=4):
        ep_ids = ", ".join(a.get("supporting_episode_ids", [])) if a.get("supporting_episode_ids") else "none"
        t_disp = ", ".join(a.get("tactic_display", [])) if a.get("tactic_display") else ", ".join(a.get("tactics", []))
        alt_rows.append(
            f"<tr>"
            f"<td>{idx}</td>"
            f"<td><code>{a['candidate_id']}</code></td>"
            f"<td>{a.get('candidate_name') or 'N/A'}</td>"
            f"<td>{a['score']:.4f}</td>"
            f"<td>{a.get('numerator', 0.0):.2f} / {a.get('denominator', 1.0):.2f}</td>"
            f"<td>[{ep_ids}]</td>"
            f"<td>{t_disp}</td>"
            f"</tr>"
        )

    prev_tech_str = ", ".join(f"<code>{t}</code>" for t in d["previous_supporting_techniques"]) if d["previous_supporting_techniques"] else "None (Start of episode)"
    cur_tech_str = ", ".join(f"<code>{t}</code>" for t in d["current_techniques"]) if d["current_techniques"] else "None"
    cur_tac_str = ", ".join(d["current_tactics"]) if d["current_tactics"] else "None"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>C4 Next-Step Prediction Panel - {d['sample_id']}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 24px; line-height: 1.5; }}
    .container {{ max-width: 1100px; margin: 0 auto; background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
    h1 {{ font-size: 1.5rem; margin-top: 0; color: #38bdf8; display: flex; align-items: center; justify-content: space-between; }}
    .badge {{ font-size: 0.8rem; padding: 4px 10px; border-radius: 9999px; font-weight: 600; text-transform: uppercase; }}
    .badge-success {{ background-color: #065f46; color: #34d399; border: 1px solid #059669; }}
    .badge-warning {{ background-color: #78350f; color: #fbbf24; border: 1px solid #d97706; }}
    .badge-danger {{ background-color: #7f1d1d; color: #f87171; border: 1px solid #dc2626; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
    .card {{ background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 16px; }}
    .card h3 {{ margin-top: 0; font-size: 0.95rem; color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.875rem; }}
    th, td {{ padding: 8px 10px; text-align: left; border-bottom: 1px solid #334155; }}
    th {{ background: #1e293b; color: #94a3b8; }}
    code {{ background: #334155; color: #38bdf8; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.85rem; }}
    .banner {{ background: #1e3a8a; border-left: 4px solid #3b82f6; padding: 12px 16px; margin: 16px 0; border-radius: 4px; font-size: 0.875rem; }}
    .explanation {{ background: #064e3b; border-left: 4px solid #10b981; padding: 12px 16px; margin: 16px 0; border-radius: 4px; font-size: 0.875rem; }}
    .meta-footer {{ margin-top: 24px; padding-top: 12px; border-top: 1px solid #334155; font-size: 0.75rem; color: #64748b; }}
  </style>
</head>
<body>
  <div class="container" id="prediction-panel-root">
    <h1>
      <span>Forensic Next-Step Prediction Panel (Component 4)</span>
      <span class="badge {d['status_badge_class']}">{d['status_badge_text']}</span>
    </h1>

    <div class="banner">
      <b>Empirical Reliability Benchmark:</b> {d['reliability_banner']}
    </div>

    {f'''<div class="banner-caution" style="background: #451a03; border-left: 4px solid #f59e0b; padding: 12px 16px; margin: 16px 0; border-radius: 4px; font-size: 0.875rem;">
      <b>Statistical Support Caution:</b> {d["caution_text"]} (Supporting Episodes: {d["support"].get("n_supporting_training_episodes", 0)}, Historical Transitions: {d["support"].get("n_transitions_from_state", 0.0):.2f})
    </div>''' if d.get('caution') else ''}

    <div class="explanation">
      <b>Model Rationale & Explainability:</b> {d['explanation']}
    </div>

    <div class="grid-2">
      <div class="card">
        <h3>Current Investigation Context</h3>
        <p><b>Sample ID:</b> <code>{d['sample_id']}</code> (Episode: <b>{d['episode_id']}</b>)</p>
        <p><b>Observed Timestamp:</b> {d['last_timestamp'] or 'N/A'}</p>
        <p><b>Incident Stage:</b> {d['incident_stage']}</p>
        <p><b>Impacted Asset:</b> {d['affected_asset']}</p>
        <p><b>Current Technique Set:</b> {cur_tech_str}</p>
        <p><b>Current Tactic Set:</b> {cur_tac_str}</p>
        <p><b>Previous Supporting Path:</b> {prev_tech_str}</p>
      </div>

      <div class="card">
        <h3>Component 3 Upstream Telemetry</h3>
        <p><b>Threat Score:</b> {d['c3_fields']['threat_score']}</p>
        <p><b>Investigation Priority:</b> {d['c3_fields']['investigation_priority']}</p>
        <p><b>Asset Criticality:</b> {d['c3_fields']['asset_criticality']}</p>
        <p><b>CTI Confidence:</b> {d['c3_fields']['cti_confidence']}</p>
        <p><b>Freshness Metric:</b> {d['c3_fields']['freshness']}</p>
        <p><b>Observable IoC:</b> {d['c3_fields']['ioc']} (Type: {d['c3_fields']['ioc_type']})</p>
        <p><b>Boundary Tie Status:</b> {d['tie_notice']}</p>
      </div>
    </div>

    <div class="card" style="margin-bottom: 16px;">
      <h3>Ranked Next-Step Predictions (Top-3)</h3>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Candidate ID</th>
            <th>Candidate Name</th>
            <th>Score</th>
            <th>Score Type</th>
            <th>Evidence (Num / Den)</th>
            <th>Supporting Episodes</th>
            <th>Tactics</th>
          </tr>
        </thead>
        <tbody>
          {"".join(cand_rows)}
        </tbody>
      </table>
    </div>

    <div class="card">
      <h3>Alternative Candidates (Ranks 4+)</h3>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Candidate ID</th>
            <th>Candidate Name</th>
            <th>Score</th>
            <th>Tactics</th>
          </tr>
        </thead>
        <tbody>
          {"".join(alt_rows)}
        </tbody>
      </table>
    </div>

    <div class="meta-footer">
      <div><b>Record ID:</b> <code>{d['record_id']}</code> | <b>Record SHA-256:</b> <code>{d['record_sha256']}</code></div>
      <div><b>Model SHA-256:</b> <code>{d['model_file_sha256']}</code> | <b>Input Events SHA-256:</b> <code>{d['input_events_sha256']}</code></div>
    </div>
  </div>
</body>
</html>
"""
    return html


def get_records_by_episode() -> dict[str, list[dict[str, Any]]]:
    """Group all prediction records by episode_id."""
    records_by_ep: dict[str, list[dict[str, Any]]] = {}
    if not JSONL_PATH.is_file():
        raise FileNotFoundError(f"Missing prediction records JSONL: {JSONL_PATH}")
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                ep = rec["input"]["episode_id"]
                records_by_ep.setdefault(ep, []).append(rec)
    return records_by_ep


def render_prediction_panel_streamlit(record: dict[str, Any]) -> None:
    """Render prediction panel into the active Streamlit app without runtime computation."""
    import streamlit as st

    d = extract_panel_view_data(record)

    st.markdown(f"### Next-Step Attack Prediction: `{d['sample_id']}` ({d['prediction_level'].capitalize()})")

    # Status & Empirical Banner
    badge_colors = {
        "ok": "background-color: #065F46; color: #34D399;",
        "fallback": "background-color: #78350F; color: #FBBF24;",
        "unseen_state": "background-color: #7F1D1D; color: #F87171;",
    }
    bstyle = badge_colors.get(d["status"], "background-color: #334155; color: #F8FAFC;")
    st.markdown(
        f"""
        <div style="display: flex; gap: 12px; align-items: center; margin-bottom: 12px;">
            <span style="{bstyle} padding: 4px 12px; border-radius: 9999px; font-weight: bold; font-size: 0.85rem;">
                {d['status_badge_text']}
            </span>
            <span style="color: #64748B; font-size: 0.85rem;">Model: <code>{d['model_file_sha256'][:12]}...</code></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(f"📊 **Empirical Reliability Benchmark (LOEO Evaluation):** {d['reliability_banner']}")
    if d.get("caution"):
        st.warning(f"⚠️ **Statistical Support Caution:** {d['caution_text']} (Supporting Episodes: {d['support'].get('n_supporting_training_episodes', 0)}, Historical Transitions: {d['support'].get('n_transitions_from_state', 0.0):.2f})")
    st.success(f"🔍 **Model Rationale:** {d['explanation']}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 🧭 Incident Context")
        st.markdown(f"**Observed Timestamp:** `{d['last_timestamp'] or 'N/A'}`")
        st.markdown(f"**Incident Stage:** {d['incident_stage']}")
        st.markdown(f"**Affected Asset:** `{d['affected_asset']}`")
        tech_list = ", ".join(f"`{t}`" for t in d["current_techniques"]) if d["current_techniques"] else "None"
        st.markdown(f"**Current Technique(s):** {tech_list}")
        tac_list = ", ".join(d["current_tactics"]) if d["current_tactics"] else "None"
        st.markdown(f"**Current Tactic(s):** {tac_list}")
        prev_list = ", ".join(f"`{t}`" for t in d["previous_supporting_techniques"]) if d["previous_supporting_techniques"] else "None (Start of sequence)"
        st.markdown(f"**Previous Supporting Techniques:** {prev_list}")

    with col2:
        st.markdown("#### 📡 Upstream Telemetry (Component 3)")
        st.markdown(f"**Threat Score:** {d['c3_fields']['threat_score']}")
        st.markdown(f"**Investigation Priority:** {d['c3_fields']['investigation_priority']}")
        st.markdown(f"**Asset Criticality:** {d['c3_fields']['asset_criticality']}")
        st.markdown(f"**CTI Confidence:** {d['c3_fields']['cti_confidence']}")
        st.markdown(f"**Freshness:** {d['c3_fields']['freshness']}")
        st.markdown(f"**Observable IoC:** {d['c3_fields']['ioc']} (Type: {d['c3_fields']['ioc_type']})")
        st.markdown(f"**Tie Notice:** {d['tie_notice']}")

    st.markdown("---")
    st.markdown("#### 🎯 Ranked Top-3 Next-Step Candidates")

    cand_table = []
    for rank, c in enumerate(d["ranked_candidates"], start=1):
        ep_ids = ", ".join(c.get("supporting_episode_ids", [])) if c.get("supporting_episode_ids") else "none"
        tactics_str = ", ".join(c.get("tactics", []))
        cand_table.append({
            "Rank": rank,
            "Candidate ID": c["candidate_id"],
            "Name": c.get("candidate_name") or "N/A",
            "Probability": f"{c['score']:.4f}",
            "Score Type": c["score_type"],
            "Numerator / Denominator": f"{c['numerator']:.2f} / {c['denominator']:.2f}",
            "Supporting Episodes": ep_ids,
            "Tactics": tactics_str,
        })
    st.table(cand_table)

    if d["alternatives"]:
        with st.expander(f"View {len(d['alternatives'])} Alternative Candidates (Ranks 4+)"):
            alt_table = []
            for rank, a in enumerate(d["alternatives"], start=4):
                alt_table.append({
                    "Rank": rank,
                    "Candidate ID": a["candidate_id"],
                    "Name": a.get("candidate_name") or "N/A",
                    "Score": f"{a['score']:.4f}",
                    "Tactics": ", ".join(a.get("tactics", [])),
                })
            st.table(alt_table)

    st.markdown("---")
    st.markdown("#### 🔒 Audit Metadata & Cryptographic Hashes")
    st.caption(
        f"**Record ID:** `{d['record_id']}` | "
        f"**Model SHA-256:** `{d['model_file_sha256']}` | "
        f"**Input Events SHA-256:** `{d['input_events_sha256']}` | "
        f"**Record SHA-256:** `{d['record_sha256']}`"
    )
    st.markdown('<span style="background-color: #DCFCE7; color: #166534; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-size: 0.85rem;">🛡️ Schema Validation: 100% PASS (c4_prediction_record.schema.json)</span>', unsafe_allow_html=True)

