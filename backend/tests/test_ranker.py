from src.evidence_ranker import (
    calculate_relevance,
    classify_evidence_type,
    rank_evidence,
)


print("=== Q-CARE EVIDENCE RANKER V3 ===")


print("\n=== EVIDENCE TYPE TEST ===")


type_tests = [
    "Information about fever and headache symptoms",
    "Yellow fever vaccination coverage",
    "Number of reported fever cases",
    "General health information",
]


for text in type_tests:

    result = classify_evidence_type(text)

    print("\nEvidence:", text)
    print("Type:", result["type"])
    print("Matched indicators:", result["matched_terms"])
    print("Reason:", result["reason"])


test_cases = [
    {
        "query": "fever",
        "evidence": [
            {
                "source": "WHO",
                "tier": 1,
                "indicator_name": (
                    "Yellow fever - number of reported cases"
                ),
            },
            {
                "source": "WHO",
                "tier": 1,
                "indicator_name": (
                    "Children aged under 5 years with "
                    "fever who received treatment"
                ),
            },
            {
                "source": "WHO",
                "tier": 1,
                "indicator_name": (
                    "Rheumatic fever and rheumatic "
                    "heart disease follow-up"
                ),
            },
        ],
    },

    {
        "query": "fever headache",
        "evidence": [
            {
                "source": "Medical Source",
                "tier": 2,
                "indicator_name": (
                    "Information about fever and "
                    "headache symptoms"
                ),
            },
            {
                "source": "WHO",
                "tier": 1,
                "indicator_name": (
                    "Yellow fever vaccination coverage"
                ),
            },
            {
                "source": "WHO",
                "tier": 1,
                "indicator_name": (
                    "Rheumatic fever follow-up"
                ),
            },
        ],
    },

    {
        "query": "eye swelling",
        "evidence": [
            {
                "source": "Medical Source",
                "tier": 2,
                "indicator_name": (
                    "Information about swollen eyelids "
                    "and eye swelling"
                ),
            },
            {
                "source": "WHO",
                "tier": 1,
                "indicator_name": (
                    "Yellow fever vaccination coverage"
                ),
            },
            {
                "source": "WHO",
                "tier": 1,
                "indicator_name": (
                    "General health facility statistics"
                ),
            },
        ],
    },

    {
        "query": "difficulty breathing",
        "evidence": [
            {
                "source": "Medical Source",
                "tier": 2,
                "indicator_name": (
                    "Difficulty breathing and "
                    "shortness of breath"
                ),
            },
            {
                "source": "WHO",
                "tier": 1,
                "indicator_name": (
                    "Respiratory health facility statistics"
                ),
            },
            {
                "source": "WHO",
                "tier": 1,
                "indicator_name": (
                    "Vaccination coverage statistics"
                ),
            },
        ],
    },
]


for case_number, case in enumerate(
    test_cases,
    start=1
):

    print("\n" + "=" * 60)
    print(f"TEST CASE {case_number}")
    print("=" * 60)

    print("Query:", case["query"])

    ranked = rank_evidence(
        case["query"],
        case["evidence"]
    )

    for index, item in enumerate(
        ranked,
        start=1
    ):

        relevance = item["relevance"]

        print(f"\n#{index}")
        print(
            "Evidence:",
            item["indicator_name"]
        )
        print(
            "Source:",
            item["source"]
        )
        print(
            "Score:",
            relevance["score"]
        )
        print(
            "Evidence type:",
            relevance["evidence_type"]
        )
        print(
            "Type reason:",
            relevance["evidence_type_reason"]
        )
        print(
            "Matched concepts:",
            relevance["matched_concepts"]
        )
        print(
            "Matched terms:",
            relevance["matched_terms"]
        )
        print(
            "Phrase matches:",
            relevance["phrase_matches"]
        )
        print(
            "Specialized penalty:",
            relevance["specialized_penalty"]
        )
        print(
            "Source weight:",
            relevance["source_weight"]
        )
        print(
            "Reason:",
            relevance["reason"]
        )


print("\n" + "=" * 60)
print("DIRECT CALCULATION TEST")
print("=" * 60)


direct_test = calculate_relevance(
    "fever headache",
    "Information about fever and headache symptoms",
    source_tier=1,
)


print("Query: fever headache")
print(
    "Evidence: Information about fever and "
    "headache symptoms"
)
print("Score:", direct_test["score"])
print(
    "Evidence type:",
    direct_test["evidence_type"]
)
print(
    "Matched concepts:",
    direct_test["matched_concepts"]
)
print(
    "Matched terms:",
    direct_test["matched_terms"]
)
print(
    "Phrase matches:",
    direct_test["phrase_matches"]
)
print(
    "Specialized penalty:",
    direct_test["specialized_penalty"]
)
print(
    "Source weight:",
    direct_test["source_weight"]
)
print(
    "Reason:",
    direct_test["reason"]
)


print("\n=== TEST COMPLETE ===")