# src/validators.py (NEW FILE)

def validate_ioc_type(ioc_type: str) -> bool:
    """Validate IoC type"""
    valid_types = ["ip", "domain", "url", "hash"]
    return ioc_type.lower() in valid_types

def validate_asset_level(level: str) -> bool:
    """Validate asset criticality"""
    valid_levels = ["low", "medium", "high", "critical"]
    return level.lower() in valid_levels

def validate_mitre_tactic(tactic: str) -> bool:
    """Check if tactic is known"""
    from priority_mapper import TACTIC_STAGE_SCORE
    return tactic.lower().replace(" ", "-") in TACTIC_STAGE_SCORE

def validate_mitre_technique(technique: str) -> bool:
    """Check if technique is known"""
    from priority_mapper import TECHNIQUE_SEVERITY
    return technique.lower() in TECHNIQUE_SEVERITY

# Use in main processing:
def process_ioc_safe(ioc: str, ioc_type: str, ...):
    # Validate inputs
    if not validate_ioc_type(ioc_type):
        raise ValueError(f"Invalid IoC type: {ioc_type}")
    
    if not validate_asset_level(asset_level):
        raise ValueError(f"Invalid asset level: {asset_level}")
    
    # ... proceed with processing