from src.evidence_engine_v22 import retrieve_evidence_v22


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

    print("\n" + "=" * 80)
    print("QUERY:", query)

    result = retrieve_evidence_v22(query)

    print("STATUS:", result["status"])

    context = result["context"]

    print("CONTEXT:", context["context"])
    print("CONCEPTS:", result["concepts"])
    print("TOPICS:", result["topics"])

    print("\nRESULTS:")

    if not result["results"]:
        print("  No relevant evidence returned.")

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

    if not result["sources"]:
        print("  No source requests made.")

    for source in result["sources"]:

        print(
            "-",
            source["source"],
            "|",
            source["status"],
            "|",
            source["status_code"],
        )