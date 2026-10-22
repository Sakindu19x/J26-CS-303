# src/ioc_cache.py (NEW FILE)

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class IoC_Cache:
    def __init__(self, db_path: str = "cti_cache.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Create cache table"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS cti_cache (
                ioc TEXT PRIMARY KEY,
                ioc_type TEXT,
                vt_result TEXT,
                otx_result TEXT,
                cached_at TEXT,
                ttl_hours INTEGER DEFAULT 24
            )
        ''')
        conn.commit()
        conn.close()
    
    def get(self, ioc: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result if still valid"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT vt_result, otx_result, cached_at FROM cti_cache WHERE ioc = ?', (ioc,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        vt_result, otx_result, cached_at = row
        cached_time = datetime.fromisoformat(cached_at)
        
        # Check if cache is still valid (24 hours by default)
        if datetime.now() - cached_time < timedelta(hours=24):
            return {
                "virustotal": json.loads(vt_result) if vt_result else None,
                "otx": json.loads(otx_result) if otx_result else None
            }
        
        return None  # Cache expired
    
    def set(self, ioc: str, ioc_type: str, vt_result: Dict, otx_result: Dict):
        """Cache the CTI results"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO cti_cache 
            VALUES (?, ?, ?, ?, ?, 24)
        ''', (
            ioc, ioc_type,
            json.dumps(vt_result),
            json.dumps(otx_result),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

# Use it in cti_apis.py:
cache = IoC_Cache()

def enrich_ioc_with_cache(ioc: str, ioc_type: str):
    # Check cache first
    cached = cache.get(ioc)
    if cached:
        return cached
    
    # If not cached, query APIs
    vt_result = query_virustotal(ioc, ioc_type)
    otx_result = query_otx(ioc, ioc_type)
    
    # Store in cache
    cache.set(ioc, ioc_type, vt_result, otx_result)
    
    return {"virustotal": vt_result, "otx": otx_result}