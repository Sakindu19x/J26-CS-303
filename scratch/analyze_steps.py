import json
import zipfile
from collections import defaultdict
from pathlib import Path

raw_dir = Path("data/raw")
scenarios = {
    "E1": "scenario_1_sudo_pam.zip",
    "E2": "scenario_2_cron.zip",
    "E3": "scenario_3_vnc_apt.zip",
    "E4": "scenario_4.zip"
}

with open("data/processed/normalized_events.json", encoding="utf-8") as f:
    norm_events = json.load(f)

norm_by_ep = defaultdict(list)
for e in norm_events:
    norm_by_ep[e["episode_id"]].append(e)

step_type_analysis = {}

for ep, zip_name in scenarios.items():
    zpath = raw_dir / zip_name
    with zipfile.ZipFile(zpath, "r") as zf:
        am_name = [n for n in zf.namelist() if n.endswith("attacker/logs/attackmate.json")][0]
        with zf.open(am_name) as fh:
            raw_steps = [json.loads(line.strip()) for line in fh if line.strip()]

    ep_events = norm_by_ep[ep]
    type_counts = defaultdict(lambda: {"total": 0, "labeled": 0, "unlabeled": 0})
    for e in ep_events:
        st = e.get("step_type") or "unknown"
        type_counts[st]["total"] += 1
        if e.get("is_labeled"):
            type_counts[st]["labeled"] += 1
        else:
            type_counts[st]["unlabeled"] += 1

    # Find labeled composite steps: loop, include, or any other container type
    composite_types = {"loop", "include"}
    composite_steps = []
    for idx, (raw_s, ev) in enumerate(zip(raw_steps, ep_events)):
        stype = raw_s.get("type")
        if stype in composite_types or "commands" in raw_s.get("parameters", {}):
            is_labeled = ev.get("is_labeled", False)
            techs = ev.get("techniques", [])
            composite_steps.append({
                "step_index": idx,
                "event_id": ev["event_id"],
                "step_type": stype,
                "is_labeled": is_labeled,
                "techniques": techs,
                "timestamp": ev["timestamp"],
                "raw_step": raw_s,
            })

    step_type_analysis[ep] = {
        "total_steps": len(ep_events),
        "type_counts": dict(type_counts),
        "composite_steps": composite_steps,
    }

print(json.dumps(step_type_analysis, indent=2, default=str))
