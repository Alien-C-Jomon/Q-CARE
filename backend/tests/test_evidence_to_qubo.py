"""
Q-Care Evidence-to-QUBO Adapter Test V1

Tests the bridge between fused evidence and QUBO scores.

These tests do NOT make medical claims.
"""

from src.evidence_to_qubo import (
    calculate_selection_score,
    adapt_fused_evidence,
    build_qubo_input,
)


def test_selection_score_is_bounded():
    evidence = {
        "source": "World Health Organization",
        "source_tier": 1,
        "matched_concepts": [
            "fever",
            "headache",
        ],
    }

    result = calculate_selection_score(
        evidence,
        [
            "fever",
            "headache",
        ],
    )

    assert 0.0 <= result["selection_score"] <= 10.0


def test_tier_one_source_is_high_quality():
    evidence = {
        "source": "World Health Organization",
        "source_tier": 1,
        "matched_concepts": [
            "fever",
        ],
    }

    result = calculate_selection_score(
        evidence,
        ["fever"],
    )

    assert result["source_quality"] == 1.0


def test_concept_coverage_is_calculated():
    evidence = {
        "source": "World Health Organization",
        "source_tier": 1,
        "matched_concepts": [
            "fever",
        ],
    }

    result = calculate_selection_score(
        evidence,
        [
            "fever",
            "headache",
        ],
    )

    assert result["coverage"] == 0.5


def test_fused_evidence_becomes_qubo_ready():
    fused = {
        "query": "I have a fever and headache",
        "context": {
            "type": "individual",
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
                    "fever",
                ],
                "category": "clinical",
            },
            {
                "source": "National Library of Medicine / MedlinePlus",
                "title": "Headache information",
                "topic": "headache",
                "source_tier": 1,
                "matched_concepts": [
                    "headache",
                ],
                "category": "clinical",
            },
        ],
        "evidence_count": 2,
        "status": "evidence_fused",
    }

    result = adapt_fused_evidence(
        fused
    )

    assert result["status"] == "qubo_ready"
    assert result["evidence_count"] == 2
    assert len(result["selection_scores"]) == 2


def test_qubo_input_contains_score_vector():
    fused = {
        "query": "fever",
        "concepts": [
            "fever",
        ],
        "evidence": [
            {
                "source": "World Health Organization",
                "source_tier": 1,
                "matched_concepts": [
                    "fever",
                ],
            },
            {
                "source": "Unknown source",
                "source_tier": 3,
                "matched_concepts": [],
            },
        ],
    }

    result = build_qubo_input(
        fused
    )

    assert result["status"] == "qubo_ready"
    assert len(result["scores"]) == 2
    assert result["maximum_selected"] == 2


if __name__ == "__main__":
    test_selection_score_is_bounded()
    test_tier_one_source_is_high_quality()
    test_concept_coverage_is_calculated()
    test_fused_evidence_becomes_qubo_ready()
    test_qubo_input_contains_score_vector()

    print(
        "PASS — Evidence-to-QUBO adapter tests passed."
    )