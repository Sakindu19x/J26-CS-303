import json
import os
import hashlib
from typing import Optional, Dict, Any


CACHE_FOLDER = os.path.join(os.path.dirname(__file__), "..", "data", "cache")


def _get_cache_path(ioc: str, ioc_type: str) -> str:
    """Create a unique filename for each IoC"""
    key = f"{ioc_type}:{ioc}".lower()
    hashed = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(CACHE_FOLDER, f"{hashed}.json")


def load_from_cache(ioc: str, ioc_type: str) -> Optional[Dict[str, Any]]:
    """Load enrichment result from cache if available"""
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    path = _get_cache_path(ioc, ioc_type)

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"[Cache] Loaded {ioc} from cache")
            return data
        except Exception:
            return None
    return None


def save_to_cache(ioc: str, ioc_type: str, data: Dict[str, Any]):
    """Save enrichment result to cache"""
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    path = _get_cache_path(ioc, ioc_type)

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Cache] Failed to save: {e}")