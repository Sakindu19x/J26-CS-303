from cti_apis import enrich_ioc
import json

# Test with a known malicious IP (example)
test_ioc = "185.220.101.1"      # Tor exit node (commonly flagged)
test_type = "ip"

print("Starting enrichment test...\n")

result = enrich_ioc(test_ioc, test_type)

print("\n========== ENRICHMENT RESULT ==========")
print(json.dumps(result, indent=2, default=str))
print("=======================================")