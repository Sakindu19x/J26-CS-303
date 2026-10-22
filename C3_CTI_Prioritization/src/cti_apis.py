import requests
from typing import Optional, Dict, Any
import sys
import os
import re
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import VIRUSTOTAL_API_KEY, OTX_API_KEY, VIRUSTOTAL_BASE_URL, OTX_BASE_URL
from cache_manager import load_from_cache, save_to_cache


def is_valid_domain(domain: str) -> bool:
    pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, domain))


def is_valid_hash(value: str) -> bool:
    value = value.lower().strip()
    return bool(re.fullmatch(r"[a-f0-9]{32}|[a-f0-9]{40}|[a-f0-9]{64}", value))


def request_with_retry(url: str, headers: dict, timeout: int = 20, retries: int = 2, delay: int = 2):
    """
    GET request with retry for temporary timeout/network errors.
    """
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            return response
        except Exception as e:
            last_error = e
            if attempt < retries:
                print(f"[!] Request failed (attempt {attempt + 1}), retrying...")
                time.sleep(delay)
    print(f"[!] Request failed after retries: {last_error}")
    return None


def query_virustotal(ioc: str, ioc_type: str) -> Optional[Dict[str, Any]]:
    if not VIRUSTOTAL_API_KEY:
        print("[!] VirusTotal API key is missing")
        return None

    headers = {"x-apikey": VIRUSTOTAL_API_KEY}

    if ioc_type == "ip":
        url = f"{VIRUSTOTAL_BASE_URL}/ip_addresses/{ioc}"

    elif ioc_type == "domain":
        if not is_valid_domain(ioc):
            print(f"[!] Invalid domain format: {ioc}")
            return {"malicious": 0, "suspicious": 0, "total": 0, "not_found": True}
        url = f"{VIRUSTOTAL_BASE_URL}/domains/{ioc}"

    elif ioc_type == "url":
        import base64
        url_id = base64.urlsafe_b64encode(ioc.encode()).decode().strip("=")
        url = f"{VIRUSTOTAL_BASE_URL}/urls/{url_id}"

    elif ioc_type in ("hash", "file"):
        if not is_valid_hash(ioc):
            print(f"[!] Invalid hash format: {ioc}")
            return {"malicious": 0, "suspicious": 0, "total": 0, "not_found": True}
        url = f"{VIRUSTOTAL_BASE_URL}/files/{ioc}"

    else:
        print(f"[!] Unsupported IoC type for VirusTotal: {ioc_type}")
        return None

    response = request_with_retry(url, headers)
    if response is None:
        return None

    try:
        if response.status_code == 200:
            data = response.json()
            attributes = data.get("data", {}).get("attributes", {})
            last_analysis = attributes.get("last_analysis_stats", {})
            return {
                "malicious": last_analysis.get("malicious", 0),
                "suspicious": last_analysis.get("suspicious", 0),
                "harmless": last_analysis.get("harmless", 0),
                "undetected": last_analysis.get("undetected", 0),
                "total": sum(last_analysis.values()) if last_analysis else 0,
                "reputation": attributes.get("reputation", 0)
            }
        elif response.status_code == 404:
            return {"malicious": 0, "suspicious": 0, "total": 0, "not_found": True}
        else:
            print(f"[!] VirusTotal error {response.status_code}")
            return {"malicious": 0, "suspicious": 0, "total": 0, "not_found": True}

    except Exception as e:
        print(f"[!] VirusTotal parse failed: {e}")
        return None


def query_otx(ioc: str, ioc_type: str) -> Optional[Dict[str, Any]]:
    if not OTX_API_KEY:
        print("[!] OTX API key is missing")
        return None

    headers = {"X-OTX-API-KEY": OTX_API_KEY}

    type_map = {
        "ip": "IPv4",
        "domain": "domain",
        "hostname": "hostname",
        "url": "url",
        "hash": "file",
        "file": "file"
    }

    section = type_map.get(ioc_type)
    if not section:
        print(f"[!] Unsupported IoC type for OTX: {ioc_type}")
        return None

    if ioc_type == "domain" and not is_valid_domain(ioc):
        print(f"[!] Invalid domain format: {ioc}")
        return {"pulse_count": 0, "reputation": 0, "not_found": True}

    if ioc_type in ("hash", "file") and not is_valid_hash(ioc):
        print(f"[!] Invalid hash format: {ioc}")
        return {"pulse_count": 0, "reputation": 0, "not_found": True}

    url = f"{OTX_BASE_URL}/indicators/{section}/{ioc}/general"

    response = request_with_retry(url, headers)
    if response is None:
        return None

    try:
        if response.status_code == 200:
            data = response.json()
            return {
                "pulse_count": data.get("pulse_info", {}).get("count", 0),
                "reputation": data.get("reputation", 0),
                "sections": data.get("sections", [])
            }
        elif response.status_code == 404:
            return {"pulse_count": 0, "reputation": 0, "not_found": True}
        else:
            print(f"[!] OTX error {response.status_code}")
            return {"pulse_count": 0, "reputation": 0, "not_found": True}

    except Exception as e:
        print(f"[!] OTX parse failed: {e}")
        return None


def enrich_ioc(ioc: str, ioc_type: str) -> Dict[str, Any]:
    # 1. Try cache first
    cached = load_from_cache(ioc, ioc_type)
    if cached:
        return cached

    print(f"[*] Enriching {ioc_type}: {ioc}")

    vt_result = query_virustotal(ioc, ioc_type)
    otx_result = query_otx(ioc, ioc_type)

    result = {
        "ioc": ioc,
        "ioc_type": ioc_type,
        "virustotal": vt_result,
        "otx": otx_result
    }

    # 2. Save to cache only if at least one source responded
    if vt_result is not None or otx_result is not None:
        save_to_cache(ioc, ioc_type, result)

    return result