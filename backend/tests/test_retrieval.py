from src.evidence_engine import (
    check_trusted_sources,
    retrieve_evidence,
)


print("=== TRUSTED SOURCE API CHECK ===")

checks = check_trusted_sources()

for result in checks:
    print("\nSource:", result["source"])
    print("Endpoint:", result["endpoint"])
    print("Reachable:", result["reachable"])
    print("Status code:", result["status_code"])
    print("Access status:", result["access_status"])


print("\n\n=== EVIDENCE RETRIEVAL TEST ===")

result = retrieve_evidence("fever")

print("\nQuery:", result["query"])
print("Status:", result["status"])

for source in result["sources"]:
    print("\nSource:", source["source"])
    print("Status:", source["status"])
    print("Status code:", source["status_code"])

    print("Results found:", len(source["results"]))

    for item in source["results"][:3]:
        print("  -", item)