\# C3 - Intelligent CTI Confidence Scoring and Prioritization Model



\*\*Project:\*\* CTI-Assisted Digital Forensic Investigation Tool for SMEs  

\*\*Project ID:\*\* J26-CS-303  

\*\*Student:\*\* Ekanayake E.M.Y.D.B (IT23201064)



\## Overview



This component receives structured security events from C1 (Web) and C2 (Network), enriches Indicators of Compromise (IoCs) using VirusTotal and AlienVault OTX, and produces an explainable prioritized investigation queue for C4.



\## Scoring Formula



S = wC·C + wF·F + wL·L + wA·A + wR·R + wT·T - wB·B



| Factor | Meaning |

|--------|---------|

| C | CTI Confidence (multi-source) |

| F | Freshness (time decay) |

| L | Local Evidence frequency |

| A | Asset Criticality |

| R | Incident Stage (MITRE Tactic) |

| T | MITRE Technique Severity |

| B | Benign / Trusted Penalty |



\## How to Run



1\. Add your API keys in `config/settings.py`

2\. Place input events in `data/evaluation\_set.json`

3\. Run:



```bash

cd src

python process\_from\_file.py

