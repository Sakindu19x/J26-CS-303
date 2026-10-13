import json
from pathlib import Path

timeline_path = Path("data/processed/attack_timelines.json")
with open(timeline_path, encoding="utf-8") as f:
    tl = json.load(f)

lines = []
lines.append("=== E4 FIRST 10 TIMELINE ROWS ===")
for r in tl["E4"][:10]:
    cmd_sub = (r.get("cmd") or "")[:35].replace("\n", " ")
    lines.append(f"{r['event_id']} | {r['timestamp']} | start+{r['seconds_since_episode_start']}s | prev+{r['seconds_since_previous_event']}s | status={r['label_status']} | techs={r['techniques']} | host={r['hostname']} | cmd={cmd_sub}")

sequences_path = Path("data/processed/attack_sequences.json")
with open(sequences_path, encoding="utf-8") as f:
    seq_data = json.load(f)

for ep_id, ep_seq in seq_data["episodes"].items():
    lines.append(f"\n=== {ep_id}: RAW SEQUENCE (length = {len(ep_seq['raw'])}) ===")
    for idx, item in enumerate(ep_seq["raw"], 1):
        lines.append(f"  [{idx:02d}] event_id={item['event_id']} | ts={item['timestamp']} | skipped_before={item['unlabeled_steps_skipped_before']} | techs={item['techniques']} | tactics={item['tactics']}")
    
    lines.append(f"\n=== {ep_id}: COLLAPSED SEQUENCE (length = {len(ep_seq['collapsed'])}) ===")
    for idx, item in enumerate(ep_seq["collapsed"], 1):
        lines.append(f"  [{idx:02d}] repeat={item['repeat_count']} | event_ids={item['event_ids']} | start={item['timestamp']} | end={item['end_timestamp']} | skipped_before={item['unlabeled_steps_skipped_before']} | techs={item['techniques']}")

with open("scratch/samples.txt", "w", encoding="utf-8") as out:
    out.write("\n".join(lines))
print("Wrote scratch/samples.txt successfully")
