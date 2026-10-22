from investigation_queue import create_investigation_queue, print_queue

# Sample list of IoCs (simulating output from C1 + C2)
sample_iocs = [
    {
        "ioc": "185.220.101.1",
        "ioc_type": "ip",
        "local_count": 8,
        "asset_level": "Critical",
        "tactic": "command-and-control",
        "technique_id": "T1071",
        "days_old": 2
    },
    {
        "ioc": "8.8.8.8",
        "ioc_type": "ip",
        "local_count": 15,
        "asset_level": "Low",
        "tactic": "discovery",
        "technique_id": "T1595",
        "days_old": 1,
        "is_trusted": True
    },
    {
        "ioc": "malicious-domain.example",
        "ioc_type": "domain",
        "local_count": 4,
        "asset_level": "High",
        "tactic": "initial-access",
        "technique_id": "T1566",
        "days_old": 10
    }
]

print("Creating ranked investigation queue...\n")

ranked = create_investigation_queue(sample_iocs)
print_queue(ranked)