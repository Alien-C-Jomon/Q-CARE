from src.clinical_context import classify_context


TEST_QUERIES = [
    "I have a fever",
    "I have a fever and headache",
    "My eye is swollen",
    "I have difficulty breathing",
    "Yellow fever vaccination coverage",
    "Number of reported fever cases",
    "How can I prevent malaria?",
    "Tell me about healthy eating",
]


print("=" * 70)
print("Q-CARE CLINICAL CONTEXT ENGINE V1")
print("=" * 70)


for query in TEST_QUERIES:

    result = classify_context(query)

    print("\n" + "-" * 70)

    print("Query:")
    print(query)

    print(
        "Context:",
        result["context"],
    )

    print(
        "Confidence:",
        result["confidence"],
    )

    print(
        "Matched terms:",
        result["matched_terms"],
    )

    print(
        "Reason:",
        result["reason"],
    )


print("\n" + "=" * 70)
print("CLINICAL CONTEXT TEST COMPLETE")
print("=" * 70)