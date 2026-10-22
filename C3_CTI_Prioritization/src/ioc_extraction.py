# src/ioc_extraction.py (NEW FILE)

import re
from typing import List, Tuple

def extract_ips(text: str) -> List[str]:
    """Extract IPv4 addresses from text"""
    ipv4_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    return re.findall(ipv4_pattern, text)

def extract_domains(text: str) -> List[str]:
    """Extract domain names"""
    domain_pattern = r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
    return re.findall(domain_pattern, text)

def extract_urls(text: str) -> List[str]:
    """Extract URLs"""
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)

def extract_hashes(text: str) -> List[Tuple[str, str]]:
    """Extract hashes (MD5, SHA-1, SHA-256) and identify type"""
    results = []
    
    # MD5: 32 hex chars
    md5_pattern = r'\b[a-fA-F0-9]{32}\b'
    for m in re.finditer(md5_pattern, text):
        results.append((m.group(), "md5"))
    
    # SHA-1: 40 hex chars
    sha1_pattern = r'\b[a-fA-F0-9]{40}\b'
    for m in re.finditer(sha1_pattern, text):
        results.append((m.group(), "sha1"))
    
    # SHA-256: 64 hex chars
    sha256_pattern = r'\b[a-fA-F0-9]{64}\b'
    for m in re.finditer(sha256_pattern, text):
        results.append((m.group(), "sha256"))
    
    return results

def normalize_ioc(ioc: str, ioc_type: str) -> str:
    """Convert IoC to canonical form"""
    if ioc_type == "domain":
        return ioc.lower().strip()
    elif ioc_type == "url":
        return ioc.lower().strip()
    elif ioc_type == "hash":
        return ioc.lower().strip()
    elif ioc_type == "ip":
        return ioc.strip()
    return ioc

# Test it:
if __name__ == "__main__":
    text = "Suspicious traffic from 192.168.1.45 to evil.com. File hash abc123..."
    print("IPs:", extract_ips(text))
    print("Domains:", extract_domains(text))