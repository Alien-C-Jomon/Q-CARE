from src.evidence_engine_v2 import retrieve_evidence_v2


tests = [
    "I have a fever",
    "I have a fever and headache",
    "My eye is swollen",
    "I have difficulty breathing",
    "How can I prevent malaria?",
    "Yellow fever vaccination coverage",
    "Number of reported fever cases",
]


for query in tests:

    print("\n" + "=" * 70)
    print("QUERY:", query)

    result = retrieve_evidence_v2(query)

    print("STATUS:", result["status"])
    print("CONTEXT:", result["context"]["context"])
    print("CONCEPTS:", result["concepts"])
    print("TOPICS:", result["topics"])

    print("\nRESULTS:")

    for evidence in result["results"]:
        print(
            "-",
            evidence["source"],
            "|",
            evidence["title"],
            "|",
            evidence["evidence_type"],
            "|",
            evidence["evidence_context"],
        )

    print("\nSOURCES:")

    for source in result["sources"]:
        print(
            "-",
            source["source"],
            "|",
            source["status"],
            "|",
            source["status_code"],
        )