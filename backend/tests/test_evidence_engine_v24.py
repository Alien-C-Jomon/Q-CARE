from src.evidence_engine_v24 import retrieve_evidence_v24


TEST_QUERIES = [

    # Individual clinical
    "I have a fever",

    # Multiple symptoms
    "I have a fever and headache",

    # Eye
    "My eye is swollen",

    # Emergency
    "I have difficulty breathing",

    # Prevention
    "How can I prevent malaria?",

    # Clear vaccination
    "Yellow fever vaccination coverage",

    # IMPORTANT: ambiguous population statistic
    "Number of reported fever cases",

    # Clear population statistic
    "Number of reported yellow fever cases",

    # IMPORTANT: ambiguous vaccination request
    "What is the vaccination coverage?",

    # Clear disease vaccination request
    "Yellow fever vaccination coverage",
]


for query in TEST_QUERIES:

    print("\n" + "=" * 100)
    print("QUERY:", query)

    result = retrieve_evidence_v24(query)

    print("STATUS:", result["status"])

    context = result["context"]

    print(
        "CONTEXT:",
        context["context"]
    )

    print(
        "CONCEPTS:",
        result["concepts"]
    )

    print(
        "TOPICS:",
        result["topics"]
    )

    print(
        "SPECIFIC TOPICS:",
        result["specific_topics"]
    )

    print(
        "STATISTIC INTENT:",
        result["statistic_intent"]
    )

    print(
        "VACCINATION INTENT:",
        result["vaccination_intent"]
    )

    print(
        "AMBIGUOUS:",
        result["ambiguity"]["ambiguous"]
    )

    if result["ambiguity"]["ambiguous"]:

        print(
            "AMBIGUITY TYPE:",
            result["ambiguity"]["type"]
        )

        print(
            "CLARIFICATION:",
            result["ambiguity"]["message"]
        )

    print("\nRESULTS:")

    if not result["results"]:

        print(
            "  No evidence returned."
        )

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

        print(
            "  No source requests made."
        )

    for source in result["sources"]:

        print(
            "-",
            source["source"],
            "|",
            source["status"],
            "|",
            source["status_code"],
        )