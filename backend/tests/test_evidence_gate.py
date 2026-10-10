"""
Q-Care Evidence Gate V1 Test
"""

from src.evidence_gate import (
    classify_evidence_quality,
    apply_evidence_gate,
    gate_ranked_response,
)


# ==========================================================
# BASIC QUALITY TEST
# ==========================================================

print("=" * 70)
print("Q-CARE EVIDENCE GATE V1")
print("=" * 70)


print("\n[1] Evidence quality classification")

test_scores = [
    90,
    70,
    65,
    50,
    30,
    0,
]


for score in test_scores:

    print(
        f"Score {score:>5} -> "
        f"{classify_evidence_quality(score)}"
    )


# ==========================================================
# RANKED EVIDENCE TEST
# ==========================================================

print("\n" + "=" * 70)
print("[2] Testing ranked evidence")
print("=" * 70)


ranked_results = [

    {
        "indicator_name":
            "Direct clinical fever information",

        "relevance": {
            "score": 96.0,
            "evidence_type":
                "clinical_information",
            "context":
                "individual",
        },
    },

    {
        "indicator_name":
            "General fever treatment information",

        "relevance": {
            "score": 72.0,
            "evidence_type":
                "clinical_information",
            "context":
                "individual",
        },
    },

    {
        "indicator_name":
            "Children with fever treatment statistics",

        "relevance": {
            "score": 62.0,
            "evidence_type":
                "public_health_statistic",
            "context":
                "population",
        },
    },

    {
        "indicator_name":
            "Yellow fever reported cases",

        "relevance": {
            "score": 46.0,
            "evidence_type":
                "epidemiological_data",
            "context":
                "population",
        },
    },

    {
        "indicator_name":
            "Unrelated health information",

        "relevance": {
            "score": 12.0,
            "evidence_type":
                "unknown",
            "context":
                "unknown",
        },
    },
]


gate_result = apply_evidence_gate(
    ranked_results,
    minimum_score=50,
)


print(
    "\nGate status:",
    gate_result["status"],
)

print(
    "Evidence available:",
    gate_result[
        "evidence_available"
    ],
)

print(
    "Accepted:",
    gate_result[
        "accepted_count"
    ],
)

print(
    "Rejected:",
    gate_result[
        "rejected_count"
    ],
)


print("\nAccepted evidence:")

for item in gate_result["accepted"]:

    print(
        "-",
        item.get(
            "indicator_name",
            "",
        ),
        "| Score:",
        item[
            "relevance"
        ]["score"],
        "| Quality:",
        item[
            "gate"
        ]["quality"],
    )


print("\nRejected evidence:")

for item in gate_result["rejected"]:

    print(
        "-",
        item.get(
            "indicator_name",
            "",
        ),
        "| Score:",
        item[
            "relevance"
        ]["score"],
        "| Quality:",
        item[
            "gate"
        ]["quality"],
    )


# ==========================================================
# NO-SUFFICIENT-EVIDENCE TEST
# ==========================================================

print("\n" + "=" * 70)
print("[3] Testing insufficient evidence")
print("=" * 70)


weak_results = [

    {
        "indicator_name":
            "Unrelated information",

        "relevance": {
            "score": 18.0,
        },
    },

    {
        "indicator_name":
            "Weakly related information",

        "relevance": {
            "score": 31.0,
        },
    },

    {
        "indicator_name":
            "Low relevance information",

        "relevance": {
            "score": 44.0,
        },
    },
]


weak_gate = apply_evidence_gate(
    weak_results,
    minimum_score=50,
)


print(
    "\nGate status:",
    weak_gate["status"],
)

print(
    "Evidence available:",
    weak_gate[
        "evidence_available"
    ],
)

print(
    "Message:",
    weak_gate[
        "message"
    ],
)


# ==========================================================
# FULL RESPONSE TEST
# ==========================================================

print("\n" + "=" * 70)
print("[4] Testing ranked response integration")
print("=" * 70)


ranked_response = {

    "query":
        "I have a fever",

    "status":
        "completed",

    "query_context":
        "individual_symptom",

    "context_confidence":
        0.95,

    "results":
        ranked_results,
}


full_result = gate_ranked_response(
    ranked_response,
    minimum_score=50,
)


print(
    "\nQuery:",
    full_result["query"],
)

print(
    "Context:",
    full_result[
        "query_context"
    ],
)

print(
    "Gate status:",
    full_result[
        "status"
    ],
)

print(
    "Accepted:",
    full_result[
        "accepted_count"
    ],
)

print(
    "Rejected:",
    full_result[
        "rejected_count"
    ],
)

print(
    "Threshold:",
    full_result[
        "threshold"
    ],
)


print("\n" + "=" * 70)
print("Q-CARE EVIDENCE GATE TEST COMPLETE")
print("=" * 70)