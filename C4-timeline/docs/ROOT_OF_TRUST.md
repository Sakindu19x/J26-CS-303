# Root of Trust: Baseline Hash Manifest Digests

> [!IMPORTANT]
> This document defines the cryptographic Root of Trust for Component 4.
> All 61 protected baseline files derive their integrity from the five JSON baseline manifests below.
> Modifying any baseline file or manifest changes these root digests.

## Baseline Manifest Root Digests

| Manifest File | Protected Files | SHA-256 Digest |
|:---|:---:|:---|
| `reports/_baseline_hashes_stage2.json` | 3 | `d1213132834c60bcfdd68b375f0453d05e78c0bbeb4287e52d1b14657d586cb3` |
| `reports/_baseline_hashes_tactic.json` | 3 | `ac3cb87bcefab414fa4214a0bf115324d92c2174fa3c756bca081efff82ed39f` |
| `reports/_baseline_hashes_7ep_stage1.json` | 10 | `4a6efe1de0f59d63a81d9b82556f389ac6e2e7b1b425d08d9928a7ea70685f1b` |
| `reports/_baseline_hashes_7ep_eval.json` | 3 | `ba1c737626e0b79808050e7643ac56972e236e301af798bce081e87e5387692c` |
| `reports/_baseline_hashes_7ep_inference.json` | 32 | `50dbe3f0f3e33a93fe5d7dc66cb201c40d046a201c5915b71f32705f531235d7` |

- **Total Protected Baseline Files**: 61 (10 Stage 1 canonical + 51 across manifest files)
- **Verification Command**: `python scripts/verify_all_hashes.py`
- **Append-Only Pre-Registration**: `reports/prereg_7episode_design.md` verified by `scripts/verify/verify_prereg_append_only.py`

## Independent Reproduction Verification

To verify root of trust digests directly in PowerShell or Bash:
```bash
python -c "import hashlib, pathlib; [print(f'{p}: {hashlib.sha256(open(p, \"rb\").read()).hexdigest()}') for p in sorted(pathlib.Path('reports').glob('_baseline_hashes_*.json'))]"
```
