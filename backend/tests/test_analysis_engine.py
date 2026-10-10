"""
Q-Care Analysis Engine V1 Test
"""

from src.analysis_engine import analyze_assessment


# ==========================================================
# HELPER
# ==========================================================

def print_result(title, result):

    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    print(
        "Status:",
        result["status"],
    )

    print(
        "Context:",
        result["context"]["context"],
    )

    print(
        "Safety:",
        result["safety"]["priority"],
    )

    print(
        "Evidence:",
        result["evidence"]["status"],
    )

    print(
        "Category:",
        result["recommendation"]["category"],
    )

    print(
        "Action:",
        result["recommendation"]["action"],
    )

    print(
        "Diagnostic:",
        result["diagnostic"],
    )


# ==========================================================
# TEST 1 — ROUTINE INDIVIDUAL SYMPTOM
# ==========================================================

routine_safety = {
    "urgency": "routine",
}


strong_evidence = {

    "evidence_available":
        True,

    "accepted_count":
        2,

    "accepted": [

        {
            "gate": {
                "quality":
                    "strong",
            }
        },

        {
            "gate": {
                "quality":
                    "usable",
            }
        },
    ],

    "status":
        "evidence_available",
}


result_1 = analyze_assessment(

    safety=
        routine_safety,

    evidence=
        strong_evidence,

    query_context=
        "individual_symptom",

    context_confidence=
        0.95,
)


print_result(
    "TEST 1 — ROUTINE INDIVIDUAL SYMPTOM",
    result_1,
)


assert result_1["status"] == "completed"

assert (
    result_1["recommendation"]["category"]
    == "precautionary_guidance"
)

assert (
    result_1["diagnostic"]
    is False
)


# ==========================================================
# TEST 2 — URGENT SAFETY SIGNAL
# ==========================================================

urgent_safety = {

    "urgency":
        "urgent",

    "matched_signals": [
        "difficulty breathing"
    ],
}


result_2 = analyze_assessment(

    safety=
        urgent_safety,

    evidence=
        strong_evidence,

    query_context=
        "emergency_signal",

    context_confidence=
        1.0,
)


print_result(
    "TEST 2 — URGENT SAFETY SIGNAL",
    result_2,
)


assert (
    result_2["recommendation"]["category"]
    == "urgent"
)

assert (
    result_2["diagnostic"]
    is False
)


# ==========================================================
# TEST 3 — PROMPT + INSUFFICIENT EVIDENCE
# ==========================================================

prompt_safety = {

    "urgency":
        "prompt",

    "matched_signals": [
        "swelling"
    ],
}


insufficient_evidence = {

    "evidence_available":
        False,

    "accepted_count":
        0,

    "accepted":
        [],

    "status":
        "insufficient_evidence",
}


result_3 = analyze_assessment(

    safety=
        prompt_safety,

    evidence=
        insufficient_evidence,

    query_context=
        "individual_symptom",

    context_confidence=
        0.95,
)


print_result(
    "TEST 3 — PROMPT + INSUFFICIENT EVIDENCE",
    result_3,
)


assert (
    result_3["recommendation"]["category"]
    == "prompt"
)

assert (
    result_3["diagnostic"]
    is False
)


# ==========================================================
# TEST 4 — NO SAFETY SIGNAL + NO EVIDENCE
# ==========================================================

result_4 = analyze_assessment(

    safety={
        "urgency":
            "routine",
    },

    evidence={
        "evidence_available":
            False,

        "accepted_count":
            0,

        "accepted":
            [],

        "status":
            "insufficient_evidence",
    },

    query_context=
        "individual_symptom",

    context_confidence=
        0.95,
)


print_result(
    "TEST 4 — NO SAFETY SIGNAL + NO EVIDENCE",
    result_4,
)


assert (
    result_4["recommendation"]["category"]
    == "insufficient_evidence"
)

assert (
    result_4["diagnostic"]
    is False
)


# ==========================================================
# TEST 5 — POPULATION HEALTH
# ==========================================================

population_evidence = {

    "evidence_available":
        True,

    "accepted_count":
        2,

    "accepted": [

        {
            "gate": {
                "quality":
                    "strong",
            }
        },

        {
            "gate": {
                "quality":
                    "usable",
            }
        },
    ],

    "status":
        "evidence_available",
}


result_5 = analyze_assessment(

    safety={
        "urgency":
            "routine",
    },

    evidence=
        population_evidence,

    query_context=
        "population_health",

    context_confidence=
        0.95,
)


print_result(
    "TEST 5 — POPULATION HEALTH",
    result_5,
)


assert (
    result_5["recommendation"]["category"]
    == "health_information"
)

assert (
    result_5["diagnostic"]
    is False
)


# ==========================================================
# FINAL
# ==========================================================

print("\n" + "=" * 70)
print("ALL Q-CARE ANALYSIS ENGINE TESTS PASSED")
print("=" * 70)