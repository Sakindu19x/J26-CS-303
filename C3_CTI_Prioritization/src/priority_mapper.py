from typing import Optional


# --------------------------------------------------
# R = Incident Stage (MITRE Tactic)
# Higher value = later stage in the attack
# --------------------------------------------------
TACTIC_STAGE_SCORE = {
    "reconnaissance": 0.30,
    "resource-development": 0.35,
    "initial-access": 0.50,
    "execution": 0.60,
    "persistence": 0.65,
    "privilege-escalation": 0.70,
    "defense-evasion": 0.70,
    "credential-access": 0.75,
    "discovery": 0.55,
    "lateral-movement": 0.80,
    "collection": 0.75,
    "command-and-control": 0.85,
    "exfiltration": 0.90,
    "impact": 1.00,
}


def get_incident_stage_score(tactic: Optional[str]) -> float:
    """
    Returns R (Incident Stage score) based on MITRE Tactic.
    Default = 0.50 if tactic is unknown.
    """
    if not tactic:
        return 0.50

    key = tactic.lower().strip().replace(" ", "-").replace("_", "-")
    return TACTIC_STAGE_SCORE.get(key, 0.50)


# --------------------------------------------------
# T = MITRE Severity (Technique danger level)
# Expanded coverage for common techniques used in SME incidents
# Sub-techniques (e.g. T1071.001) fall back to parent (T1071)
# --------------------------------------------------
TECHNIQUE_SEVERITY = {
    # Impact / ransomware
    "t1486": 1.00,  # Data Encrypted for Impact
    "t1490": 0.95,  # Inhibit System Recovery
    "t1489": 0.90,  # Service Stop
    "t1491": 0.85,  # Defacement
    "t1499": 0.80,  # Endpoint Denial of Service
    "t1498": 0.80,  # Network Denial of Service

    # Exfiltration
    "t1041": 0.88,  # Exfiltration Over C2 Channel
    "t1048": 0.90,  # Exfiltration Over Alternative Protocol
    "t1567": 0.86,  # Exfiltration Over Web Service
    "t1020": 0.82,  # Automated Exfiltration
    "t1030": 0.70,  # Data Transfer Size Limits

    # Command and Control
    "t1071": 0.85,  # Application Layer Protocol
    "t1090": 0.84,  # Proxy
    "t1105": 0.83,  # Ingress Tool Transfer
    "t1573": 0.82,  # Encrypted Channel
    "t1572": 0.80,  # Protocol Tunneling
    "t1219": 0.78,  # Remote Access Software
    "t1102": 0.75,  # Web Service
    "t1132": 0.72,  # Data Encoding

    # Credential Access
    "t1003": 0.90,  # OS Credential Dumping
    "t1110": 0.78,  # Brute Force
    "t1555": 0.85,  # Credentials from Password Stores
    "t1558": 0.86,  # Steal or Forge Kerberos Tickets
    "t1552": 0.80,  # Unsecured Credentials
    "t1187": 0.75,  # Forced Authentication

    # Lateral Movement
    "t1021": 0.80,  # Remote Services
    "t1570": 0.78,  # Lateral Tool Transfer
    "t1550": 0.82,  # Use Alternate Authentication Material
    "t1210": 0.80,  # Exploitation of Remote Services
    "t1534": 0.72,  # Internal Spearphishing

    # Execution
    "t1059": 0.82,  # Command and Scripting Interpreter
    "t1204": 0.78,  # User Execution
    "t1047": 0.80,  # Windows Management Instrumentation
    "t1053": 0.76,  # Scheduled Task/Job
    "t1106": 0.74,  # Native API
    "t1569": 0.72,  # System Services

    # Persistence
    "t1547": 0.80,  # Boot or Logon Autostart Execution
    "t1053": 0.76,  # Scheduled Task/Job
    "t1136": 0.78,  # Create Account
    "t1543": 0.80,  # Create or Modify System Process
    "t1133": 0.75,  # External Remote Services
    "t1505": 0.82,  # Server Software Component

    # Privilege Escalation
    "t1548": 0.82,  # Abuse Elevation Control Mechanism
    "t1068": 0.85,  # Exploitation for Privilege Escalation
    "t1134": 0.80,  # Access Token Manipulation
    "t1055": 0.82,  # Process Injection

    # Defense Evasion
    "t1027": 0.75,  # Obfuscated Files or Information
    "t1070": 0.78,  # Indicator Removal
    "t1112": 0.74,  # Modify Registry
    "t1562": 0.80,  # Impair Defenses
    "t1036": 0.72,  # Masquerading
    "t1218": 0.76,  # System Binary Proxy Execution
    "t1620": 0.70,  # Reflective Code Loading

    # Discovery
    "t1082": 0.50,  # System Information Discovery
    "t1083": 0.52,  # File and Directory Discovery
    "t1018": 0.55,  # Remote System Discovery
    "t1046": 0.58,  # Network Service Discovery
    "t1057": 0.50,  # Process Discovery
    "t1016": 0.48,  # System Network Configuration Discovery
    "t1033": 0.48,  # System Owner/User Discovery

    # Collection
    "t1005": 0.72,  # Data from Local System
    "t1039": 0.74,  # Data from Network Shared Drive
    "t1113": 0.70,  # Screen Capture
    "t1115": 0.68,  # Clipboard Data
    "t1560": 0.72,  # Archive Collected Data

    # Initial Access
    "t1566": 0.72,  # Phishing
    "t1190": 0.80,  # Exploit Public-Facing Application
    "t1133": 0.75,  # External Remote Services
    "t1078": 0.78,  # Valid Accounts
    "t1189": 0.74,  # Drive-by Compromise
    "t1195": 0.82,  # Supply Chain Compromise
    "t1566.001": 0.74,  # Spearphishing Attachment
    "t1566.002": 0.74,  # Spearphishing Link

    # Reconnaissance / low severity
    "t1595": 0.40,  # Active Scanning
    "t1592": 0.35,  # Gather Victim Host Information
    "t1589": 0.35,  # Gather Victim Identity Information
    "t1590": 0.35,  # Gather Victim Network Information
    "t1591": 0.35,  # Gather Victim Org Information
    "t1598": 0.45,  # Phishing for Information
    "t1593": 0.30,  # Search Open Websites/Domains
}


def _normalize_technique_id(technique_id: str) -> str:
    """
    Normalize technique IDs:
    - lower case
    - keep sub-technique if explicitly mapped
    - else fall back to parent technique (T1071.001 -> t1071)
    """
    key = technique_id.lower().strip()
    if key in TECHNIQUE_SEVERITY:
        return key
    if "." in key:
        parent = key.split(".", 1)[0]
        return parent
    return key


def get_mitre_severity(technique_id: Optional[str]) -> float:
    """
    Returns T (MITRE Severity score).
    technique_id format: "T1486", "t1486", or "T1071.001"
    Default = 0.50 if technique is unknown.
    """
    if not technique_id:
        return 0.50

    key = _normalize_technique_id(technique_id)
    return TECHNIQUE_SEVERITY.get(key, 0.50)


def get_both_scores(tactic: Optional[str] = None, technique_id: Optional[str] = None) -> dict:
    """
    Convenience function – returns both R and T together.
    """
    return {
        "incident_stage": get_incident_stage_score(tactic),
        "mitre_severity": get_mitre_severity(technique_id)
    }
