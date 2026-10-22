#!/usr/bin/env python3
"""
Integrated C3 Pipeline

Combines all components: extraction, validation, enrichment, scoring, prioritization
"""

import sys
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import all our modules
from ioc_extraction import extract_all_iocs, normalize_ioc
from validators import validate_all_inputs, validate_ioc_type, validate_ioc_value
from ioc_cache import IoC_Cache
from cti_apis import enrich_ioc
from cti_confidence import calculate_cti_confidence
from feature_calculators import (
    calculate_freshness,
    calculate_local_evidence,
    get_asset_criticality,
    get_benign_penalty
)
from priority_mapper import get_incident_stage_score, get_mitre_severity
from scoring_engine import calculate_score
from investigation_queue import create_investigation_queue, print_queue


class C3_Pipeline:
    """
    Complete C3 Prioritization Pipeline
    
    Example:
        >>> pipeline = C3_Pipeline()
        >>> results = pipeline.process_raw_event({
        ...     "raw_text": "Connection to 192.168.1.1 and evil.com",
        ...     "asset_level": "High",
        ...     "tactic": "command-and-control"
        ... })
    """
    
    def __init__(self):
        """Initialize pipeline"""
        self.cache = IoC_Cache()
        print("[✓] C3 Pipeline initialized")
    
    
    def extract_iocs_from_event(self, event_text: str) -> List[Tuple[str, str]]:
        """
        Extract all IoCs from raw event text
        
        Args:
            event_text: Raw security event text
        
        Returns:
            List of (ioc_value, ioc_type) tuples
        """
        print("\n[STEP 1] Extracting IoCs from event...")
        
        iocs = extract_all_iocs(event_text)
        print(f"[✓] Extracted {len(iocs)} unique IoCs")
        
        for ioc, ioc_type in iocs:
            print(f"  • [{ioc_type}] {ioc}")
        
        return iocs
    
    
    def validate_inputs(
        self,
        ioc: str,
        ioc_type: str,
        asset_level: str,
        tactic: str,
        technique_id: str,
        local_count: int,
        max_local_count: int
    ) -> Tuple[bool, List[str]]:
        """
        Validate all inputs before processing
        
        Returns:
            (is_valid, list_of_errors)
        """
        print("\n[STEP 2] Validating inputs...")
        
        is_valid, errors = validate_all_inputs(
            ioc, ioc_type, asset_level, tactic,
            technique_id, local_count, max_local_count
        )
        
        if is_valid:
            print("[✓] All inputs valid")
        else:
            print("[✗] Validation errors:")
            for error in errors:
                print(f"  • {error}")
        
        return (is_valid, errors)
    
    
    def enrich_ioc_with_cti(self, ioc: str, ioc_type: str) -> Dict[str, Any]:
        """
        Enrich IoC with CTI (with caching)
        
        Args:
            ioc: The indicator
            ioc_type: Type (ip, domain, url, hash)
        
        Returns:
            Dict with virustotal and otx results
        """
        print("\n[STEP 3] Enriching with CTI...")
        
        enrichment = enrich_ioc(ioc, ioc_type, use_cache=True)
        return enrichment
    
    
    def calculate_threat_score(
        self,
        ioc: str,
        ioc_type: str,
        vt_result: Dict,
        otx_result: Dict,
        local_count: int,
        max_local_count: int,
        asset_level: str,
        tactic: str,
        technique_id: str,
        days_old: int = 1,
        is_trusted: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate complete threat score for an IoC
        
        Args:
            (see parameters)
        
        Returns:
            Dict with score, priority, and breakdown
        """
        print("\n[STEP 4] Calculating threat score...")
        
        # Calculate each factor
        C = calculate_cti_confidence(vt_result, otx_result)
        F = calculate_freshness(
            datetime.now(timezone.utc) - timedelta(days=days_old)
        )
        L = calculate_local_evidence(local_count, max_local_count)
        A = get_asset_criticality(asset_level)
        R = get_incident_stage_score(tactic)
        T = get_mitre_severity(technique_id)
        B = get_benign_penalty(is_trusted)
        
        # Calculate final score
        result = calculate_score(C, F, L, A, R, T, B)
        
        # Print factor values
        print("\n  Factor Values:")
        print(f"    C (CTI Confidence)      : {C:.3f}")
        print(f"    F (Freshness)           : {F:.3f}")
        print(f"    L (Local Evidence)      : {L:.3f}")
        print(f"    A (Asset Criticality)   : {A:.3f}")
        print(f"    R (Incident Stage)      : {R:.3f}")
        print(f"    T (MITRE Severity)      : {T:.3f}")
        print(f"    B (Benign Penalty)      : {B:.3f}")
        
        print(f"\n  Final Score: {result['score']}/100")
        print(f"  Priority: {result['priority']}")
        
        return result
    
    
    def process_ioc(
        self,
        ioc: str,
        ioc_type: str,
        local_count: int = 3,
        max_local_count: int = 20,
        asset_level: str = "Medium",
        tactic: str = "discovery",
        technique_id: str = "T1595",
        days_old: int = 1,
        is_trusted: bool = False
    ) -> Dict[str, Any]:
        """
        Process a single IoC through the complete pipeline
        
        Args:
            ioc: Indicator value
            ioc_type: Type (ip, domain, url, hash)
            local_count: How many times seen in local logs
            max_local_count: Max in dataset
            asset_level: Low, Medium, High, Critical
            tactic: MITRE tactic
            technique_id: MITRE technique (T1234)
            days_old: How old is the intelligence
            is_trusted: Is it trusted infrastructure
        
        Returns:
            Complete result with score, priority, breakdown
        """
        print("\n" + "="*70)
        print(f"PROCESSING IoC: {ioc} ({ioc_type})")
        print("="*70)
        
        # Step 1: Validate inputs
        is_valid, errors = self.validate_inputs(
            ioc, ioc_type, asset_level, tactic, technique_id,
            local_count, max_local_count
        )
        
        if not is_valid:
            print("[✗] Validation failed - skipping this IoC")
            return None
        
        # Step 2: Enrich with CTI
        enrichment = self.enrich_ioc_with_cti(ioc, ioc_type)
        vt_result = enrichment.get("virustotal")
        otx_result = enrichment.get("otx")
        
        # Step 3: Calculate threat score
        result = self.calculate_threat_score(
            ioc, ioc_type,
            vt_result, otx_result,
            local_count, max_local_count,
            asset_level, tactic, technique_id,
            days_old, is_trusted
        )
        
        return {
            "ioc": ioc,
            "ioc_type": ioc_type,
            "score": result["score"],
            "priority": result["priority"],
            "breakdown": result["breakdown"],
            "enrichment": enrichment,
            "from_cache": enrichment.get("from_cache", False)
        }
    
    
    def process_multiple_iocs(
        self,
        ioc_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple IoCs and return ranked queue
        
        Args:
            ioc_list: List of dicts with ioc, ioc_type, and context
        
        Example:
            >>> iocs = [
            ...     {
            ...         "ioc": "192.168.1.1",
            ...         "ioc_type": "ip",
            ...         "local_count": 5,
            ...         "asset_level": "High"
            ...     },
            ...     ...
            ... ]
            >>> results = pipeline.process_multiple_iocs(iocs)
        """
        print("\n" + "="*70)
        print(f"PROCESSING {len(ioc_list)} IoCs")
        print("="*70)
        
        results = []
        for idx, ioc_data in enumerate(ioc_list, 1):
            print(f"\n[{idx}/{len(ioc_list)}]")
            
            result = self.process_ioc(
                ioc=ioc_data.get("ioc"),
                ioc_type=ioc_data.get("ioc_type", "ip"),
                local_count=ioc_data.get("local_count", 3),
                max_local_count=ioc_data.get("max_local_count", 20),
                asset_level=ioc_data.get("asset_level", "Medium"),
                tactic=ioc_data.get("tactic", "discovery"),
                technique_id=ioc_data.get("technique_id", "T1595"),
                days_old=ioc_data.get("days_old", 1),
                is_trusted=ioc_data.get("is_trusted", False)
            )
            
            if result:
                results.append(result)
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results
    
    
    def process_raw_event(
        self,
        raw_event_text: str,
        default_asset_level: str = "Medium",
        default_tactic: str = "discovery",
        default_technique: str = "T1595",
        local_count: int = 3,
        max_local_count: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Process raw security event (extract IoCs, score, rank)
        
        High-level convenience function
        
        Args:
            raw_event_text: Raw text from security logs
            default_asset_level: Asset level if not specified
            default_tactic: MITRE tactic if not specified
            default_technique: MITRE technique if not specified
            local_count: Default local count
            max_local_count: Default max
        
        Returns:
            Ranked list of prioritized IoCs
        
        Example:
            >>> event = "Connection from 192.168.1.1 to evil.com"
            >>> results = pipeline.process_raw_event(event)
            >>> pipeline.print_results(results)
        """
        # Extract IoCs
        iocs = self.extract_iocs_from_event(raw_event_text)
        
        if not iocs:
            print("[!] No IoCs found in event")
            return []
        
        # Convert to processing format
        ioc_list = [
            {
                "ioc": ioc,
                "ioc_type": ioc_type,
                "local_count": local_count,
                "max_local_count": max_local_count,
                "asset_level": default_asset_level,
                "tactic": default_tactic,
                "technique_id": default_technique
            }
            for ioc, ioc_type in iocs
        ]
        
        # Process all
        results = self.process_multiple_iocs(ioc_list)
        
        return results
    
    
    @staticmethod
    def print_results(results: List[Dict[str, Any]]):
        """Pretty print results"""
        print("\n" + "="*70)
        print("INVESTIGATION QUEUE (RANKED)")
        print("="*70)
        print(f"{'Rank':<5} {'Score':<8} {'Priority':<10} {'IoC':<30} {'Type':<8}")
        print("-"*70)
        
        for idx, result in enumerate(results, 1):
            ioc = result["ioc"][:25]
            print(f"{idx:<5} {result['score']:<8.1f} {result['priority']:<10} {ioc:<30} {result['ioc_type']:<8}")
        
        print("="*70)
    
    
    def print_cache_stats(self):
        """Print cache statistics"""
        self.cache.print_stats()


# ===== TESTING =====

if __name__ == "__main__":
    # Initialize pipeline
    pipeline = C3_Pipeline()
    
    # Test data: raw security event
    raw_event = """
    Security Alert:
    - Connection detected: 192.168.1.100 → 185.220.101.45 (C2 server)
    - Domain accessed: malware-c2.com
    - Suspicious file download: http://badsite.net/shell.exe
    - File hash: 5d41402abc4b2a76b9719d911017c592
    - Affected asset: web-server-01
    - MITRE: command-and-control (T1071)
    """
    
    print("[*] Processing raw security event...")
    print(f"Raw event: {raw_event[:100]}...\n")
    
    # Process the raw event
    results = pipeline.process_raw_event(
        raw_event_text=raw_event,
        default_asset_level="High",
        default_tactic="command-and-control",
        default_technique="T1071"
    )
    
    # Print ranked results
    pipeline.print_results(results)
    
    # Show cache stats
    pipeline.print_cache_stats()