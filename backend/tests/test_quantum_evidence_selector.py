"""
Q-Care Quantum Evidence Selector Test V1

Tests the complete mapping:

    Fused Evidence
        ↓
    QUBO
        ↓
    QAOA
        ↓
    Selected Evidence

This is an optimization test, not a medical test.
"""

from src.quantum_evidence_selector import (
    select_evidence_with_qaoa,
)


def test_quantum_evidence_selection():

    fused = {
        "query": "I have a fever and headache",

        "context": {
            "type": "individual"
        },

        "concepts": [
            "fever",
            "headache",
        ],

        "evidence": [

            {
                "source": "World Health Organization",
                "title": "Fever information",
                "topic": "fever",
                "source_tier": 1,
                "matched_concepts": [
                    "fever"
                ],
                "category": "clinical",
            },

            {
                "source": "National Library of Medicine / MedlinePlus",
                "title": "Headache information",
                "topic": "headache",
                "source_tier": 1,
                "matched_concepts": [
                    "headache"
                ],
                "category": "clinical",
            },

            {
                "source": "Centers for Disease Control and Prevention",
                "title": "General health information",
                "topic": "general",
                "source_tier": 1,
                "matched_concepts": [],
                "category": "clinical",
            },

            {
                "source": "Unknown source",
                "title": "General information",
                "topic": "general",
                "source_tier": 3,
                "matched_concepts": [],
                "category": "unknown",
            },
        ],
    }

    result = select_evidence_with_qaoa(
        fused,
        penalty=10.0,
        p=1,
    )

    print()
    print(
        "Q-Care Quantum Evidence Selector"
    )
    print(
        "---------------------------------"
    )

    print(
        "Scores:",
        result["scores"],
    )

    print(
        "Selection:",
        result["selection"],
    )

    print(
        "Selected indices:",
        result["selected_indices"],
    )

    print(
        "Selected evidence:"
    )

    for evidence in result["selected_evidence"]:

        print(
            " -",
            evidence["source"],
            "|",
            evidence["title"],
        )

    print(
        "QAOA probability:",
        result["optimization"]["probability"],
    )

    print(
        "QAOA cost:",
        result["optimization"]["cost"],
    )

    # ------------------------------------------------------
    # Validation
    # ------------------------------------------------------

    assert result["status"] == "selected"

    assert result["selection"] == (
        1,
        1,
        0,
        0,
    )

    assert result["selected_indices"] == [
        0,
        1,
    ]

    assert len(
        result["selected_evidence"]
    ) == 2

    assert (
        result["selected_evidence"][0]["source"]
        == "World Health Organization"
    )

    assert (
        result["selected_evidence"][1]["source"]
        == "National Library of Medicine / MedlinePlus"
    )

    print()
    print(
        "PASS — Quantum evidence selection and mapping passed."
    )


if __name__ == "__main__":
    test_quantum_evidence_selection()