import urllib.request
import json
import hashlib
from pathlib import Path

url = "https://zenodo.org/api/records/18390560"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    print("Record title:", data.get("metadata", {}).get("title"))
    files = data.get("files", [])
    print(f"Total files in Zenodo record: {len(files)}")
    target_names = ["scenario_1_sudo_pam.zip", "scenario_2_cron.zip", "scenario_3_vnc_apt.zip", "scenario_4.zip"]
    zenodo_checksums = {}
    for f in files:
        fname = f.get("key") or f.get("filename")
        if fname in target_names:
            zenodo_checksums[fname] = {
                "size": f.get("size"),
                "checksum": f.get("checksum"),
            }
            print(f"Zenodo File: {fname}, size={f.get('size')}, checksum={f.get('checksum')}")
except Exception as e:
    print("Zenodo query error:", e)

# Compute MD5 and SHA256 of local archives
raw_dir = Path("data/raw")
for fname in ["scenario_1_sudo_pam.zip", "scenario_2_cron.zip", "scenario_3_vnc_apt.zip", "scenario_4.zip"]:
    p = raw_dir / fname
    if p.exists():
        md5_h = hashlib.md5()
        sha256_h = hashlib.sha256()
        with open(p, "rb") as fh:
            while chunk := fh.read(1024 * 1024):
                md5_h.update(chunk)
                sha256_h.update(chunk)
        print(f"Local {fname}: size={p.stat().st_size}, md5={md5_h.hexdigest()}, sha256={sha256_h.hexdigest()}")
