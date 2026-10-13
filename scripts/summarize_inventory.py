import json, sys, collections, posixpath
j = json.load(open("reports/dataset_inventory.json", encoding="utf-8"))
print("issues:", j["issues"])
for a in j["archives"]:
    print("\n==", a["archive"], "files", a["n_files"], "bytes", a["total_uncompressed_bytes"])
    print(" ext:", a["extension_counts"])
    g = a["folder_groups_candidate_runs"]
    print(" folder groups:", len(g))
    for k, v in list(g.items())[:8]:
        print("   ", k, v)
    print(" attackmate:", a["attackmate_json_files"])
    base = collections.Counter(posixpath.basename(f["name"]) for f in a["files"])
    print(" top basenames:", base.most_common(12))
    for n, raw in a["attackmate_json_raw_head"].items():
        print(" --", n); print(raw[:600])
        break
