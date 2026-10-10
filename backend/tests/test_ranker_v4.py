"""
Q-Care Evidence Ranker V4 Test

Tests context-aware ranking against realistic evidence.

V4 should distinguish between:
- individual symptoms
- population health
- vaccination
- emergency signals
"""

from src.evidence_ranker_v4 import (
    rank_evidence,
    rank_retrieval_response,
)


# ==========================================================
# TEST EVIDENCE
# ==========================================================

EVIDENCE = [
    {
        "indicator_name":
            "Information about fever and headache symptoms",
        "source": "Clinical Reference",
        "tier": 2,
    },

    {
        "indicator_name":
            "Has systems for follow-up/recall to deliver "
            "long-term penicillin prophylaxis to patients "
            "with rheumatic fever and rheumatic heart disease",
        "source": "World Health Organization",
        "tier": 1,
    },

    {
        "indicator_name":
            "Yellow fever - number of reported cases",
        "source": "World Health Organization",
        "tier": 1,
    },

    {
        "indicator_name":
            "Yellow fever vaccine immunization coverage "
            "among 1-year olds",
        "source": "World Health Organization",
        "tier": 1,
    },

    {
        "indicator_name":
            "Children aged under 5 years with fever who "
            "received treatment with any antimalarial (%)",
        "source": "World Health Organization",
        "tier": 1,
    },

    {
        "indicator_name":
            "General health information",
        "source": "General Source",
        "tier": 3,
    },
]


# ==========================================================
# HELPER
# ==========================================================

def run_test(query):

    print("\n" + "=" * 70)

    print("QUERY:")
    print(query)

    print("=" * 70)

    ranked = rank_evidence(
        query,
        EVIDENCE,
    )

    context_result = ranked[0]["relevance"]

    print(
        "\nDetected query context:",
        context_result.get(
            "query_context"
        ),
    )

    print("\nRanked evidence:")

    for index, item in enumerate(
        ranked,
        start=1,
    ):

        relevance = item.get(
            "relevance",
            {},
        )

        print(
            f"\n#{index}"
        )

        print(
            "Evidence:",
            item.get(
                "indicator_name",
                "",
            ),
        )

        print(
            "Score:",
            relevance.get(
                "score"
            ),
        )

        print(
            "Evidence type:",
            relevance.get(
                "evidence_type"
            ),
        )

        print(
            "Evidence context:",
            relevance.get(
                "context"
            ),
        )

        print(
            "Context adjustment:",
            relevance.get(
                "context_adjustment"
            ),
        )

        print(
            "Reason:",
            relevance.get(
                "reason"
            ),
        )


# ==========================================================
# TEST 1
# ==========================================================

run_test(
    "I have a fever"
)


# ==========================================================
# TEST 2
# ==========================================================

run_test(
    "I have a fever and headache"
)


# ==========================================================
# TEST 3
# ==========================================================

run_test(
    "My eye is swollen"
)


# ==========================================================
# TEST 4
# ==========================================================

run_test(
    "I have difficulty breathing"
)


# ==========================================================
# TEST 5
# ==========================================================

run_test(
    "Number of reported fever cases"
)


# ==========================================================
# TEST 6
# ==========================================================

run_test(
    "Yellow fever vaccination coverage"
)


# ==========================================================
# RETRIEVAL RESPONSE TEST
# ==========================================================

print("\n" + "=" * 70)
print("RETRIEVAL RESPONSE TEST")
print("=" * 70)


retrieval_response = {

    "query": "I have a fever",

    "status": "completed",

    "sources": [

        {
            "source":
                "World Health Organization",

            "tier": 1,

            "status":
                "success",

            "results": [

                {
                    "indicator_name":
                        "Yellow fever - number of reported cases",
                },

                {
                    "indicator_name":
                        "Children aged under 5 years "
                        "with fever who received treatment",
                },

                {
                    "indicator_name":
                        "Information about fever and "
                        "headache symptoms",
                },
            ],
        },
    ],
}


ranked_response = rank_retrieval_response(
    "I have a fever",
    retrieval_response,
)


print(
    "\nQuery context:",
    ranked_response.get(
        "query_context"
    ),
)

print(
    "Context confidence:",
    ranked_response.get(
        "context_confidence"
    ),
)

print(
    "Total results:",
    ranked_response.get(
        "count"
    ),
)


for index, item in enumerate(
    ranked_response.get(
        "results",
        []
    ),
    start=1,
):

    relevance = item.get(
        "relevance",
        {},
    )

    print(
        f"\n#{index}",
    )

    print(
        "Evidence:",
        item.get(
            "indicator_name",
            "",
        ),
    )

    print(
        "Score:",
        relevance.get(
            "score"
        ),
    )

    print(
        "Evidence type:",
        relevance.get(
            "evidence_type"
        ),
    )

    print(
        "Context adjustment:",
        relevance.get(
            "context_adjustment"
        ),
    )


print("\n" + "=" * 70)
print("Q-CARE V4 TEST COMPLETE")
print("=" * 70)