"""
Q-Care Real Evidence Pipeline Test

Pipeline:

User query
    ↓
WHO / CDC retrieval
    ↓
Evidence Ranker V3.2
    ↓
Ranked evidence
"""

from src.evidence_engine import retrieve_evidence
from src.evidence_ranker import rank_retrieval_response


QUERY = "fever"


print("=" * 70)
print("Q-CARE REAL EVIDENCE PIPELINE")
print("=" * 70)

print("\nQuery:", QUERY)

print("\n[1] Retrieving evidence from trusted APIs...")

retrieval = retrieve_evidence(
    QUERY,
    limit=10,
)

print("\nRetrieval status:")
print(retrieval.get("status"))

print("\nSources received:")

for source in retrieval.get(
    "sources",
    [],
):
    print(
        "-",
        source.get("source"),
        "|",
        source.get("status"),
        "| HTTP",
        source.get("status_code"),
    )

print("\n[2] Ranking retrieved evidence with V3.2...")

ranked = rank_retrieval_response(
    QUERY,
    retrieval,
)

print(
    "\nRanking status:",
    ranked.get("status"),
)

print(
    "Total evidence items:",
    ranked.get("count"),
)

print("\n" + "=" * 70)
print("RANKED REAL EVIDENCE")
print("=" * 70)


for index, item in enumerate(
    ranked.get("results", []),
    start=1,
):

    relevance = item.get(
        "relevance",
        {},
    )

    print(f"\n#{index}")

    print(
        "Evidence:",
        item.get(
            "indicator_name",
            item.get(
                "title",
                "Unknown",
            ),
        ),
    )

    print(
        "Source:",
        item.get(
            "source",
            "Unknown",
        ),
    )

    print(
        "Score:",
        relevance.get(
            "score",
            0,
        ),
    )

    print(
        "Evidence type:",
        relevance.get(
            "evidence_type",
            "unknown",
        ),
    )

    print(
        "Context:",
        relevance.get(
            "context",
            "unknown",
        ),
    )

    print(
        "Matched concepts:",
        relevance.get(
            "matched_concepts",
            [],
        ),
    )

    print(
        "Matched terms:",
        relevance.get(
            "matched_terms",
            [],
        ),
    )

    print(
        "Specialized penalty:",
        relevance.get(
            "specialized_penalty",
            0,
        ),
    )

    print(
        "Reason:",
        relevance.get(
            "reason",
            "",
        ),
    )


print("\n" + "=" * 70)
print("REAL PIPELINE TEST COMPLETE")
print("=" * 70)