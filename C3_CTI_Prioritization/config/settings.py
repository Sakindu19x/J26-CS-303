# ==============================================
# C3 CTI Prioritization - Configuration
# ==============================================

# ---------- Decay parameter for Freshness ----------
# Higher value = intelligence becomes old faster
LAMBDA_DECAY = 0.05

# ---------- Default Weights (Balanced) ----------
DEFAULT_WEIGHTS = {
    "w_c": 0.25,   # CTI Confidence
    "w_f": 0.15,   # Freshness
    "w_l": 0.20,   # Local Evidence
    "w_a": 0.15,   # Asset Criticality
    "w_r": 0.10,   # Incident Stage
    "w_t": 0.10,   # MITRE Severity
    "w_b": 0.05    # Benign Penalty
}

# ---------- API Keys ----------
# Replace the empty strings with your real keys later
VIRUSTOTAL_API_KEY = "ee74ef32e8917b66c192796dc8f364cfab609248f1ad067a0816837a911650fc"
OTX_API_KEY = "5a86b14bfcf42ce1732656e985d91d9d5bc65f0df094e16e8579b2d7e20e546c"

# ---------- API Endpoints ----------
VIRUSTOTAL_BASE_URL = "https://www.virustotal.com/api/v3"
OTX_BASE_URL = "https://otx.alienvault.com/api/v1"

# ---------- Other Settings ----------
CACHE_ENABLED = True
CACHE_FOLDER = "data/cache"