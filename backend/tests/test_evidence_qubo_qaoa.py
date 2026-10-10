"""
Q-Care Evidence → QUBO → QAOA Integration Test V1

Verifies that the Evidence-to-QUBO adapter produces a valid
score vector that can be consumed by the existing QAOA optimizer.

This test does NOT make medical claims.
"""

from src.evidence_to_qubo import build_qubo_input
from src.quantum.qaoa_optimizer import (
    build_qaoa_circuit,
    evaluate_statevector_layers,
    calculate_expectation,
    extract_best_solution,
)


def test_evidence_to_qubo_to_qaoa():
    fused = {
        "query": "I have a fever and headache",
        "context": {
            "type": "individual"
        },
        "concepts": [
            "fever",
            "headache"
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
                "source": "Unknown source",
                "title": "General information",
                "topic": "general",
                "source_tier": 3,
                "matched_concepts": [],
                "category": "unknown",
            },
            {
                "source": "Unknown source",
                "title": "Additional information",
                "topic": "general",
                "source_tier": 3,
                "matched_concepts": [],
                "category": "unknown",
            },
        ],
    }

    # ------------------------------------------------------
    # STEP 1 — Evidence → QUBO
    # ------------------------------------------------------

    qubo_input = build_qubo_input(
        fused
    )

    scores = qubo_input["scores"]

    assert qubo_input["status"] == "qubo_ready"
    assert len(scores) == 4
    assert all(
        0.0 <= score <= 10.0
        for score in scores
    )

    # ------------------------------------------------------
    # STEP 2 — QUBO → QAOA circuit
    # ------------------------------------------------------

    circuit = build_qaoa_circuit(
        scores,
        penalty=10.0,
        p=1,
    )

    # ------------------------------------------------------
    # STEP 3 — Evaluate QAOA
    # ------------------------------------------------------

    statevector = (
        evaluate_statevector_layers(
            circuit,
            [1.5707963267948966],
            [0.7853981633974483],
        )
    )

    expectation = (
        calculate_expectation(
            statevector,
            scores,
            penalty=10.0,
        )
    )

    # ------------------------------------------------------
    # STEP 4 — Extract solution
    # ------------------------------------------------------

    solution = extract_best_solution(
        statevector,
        scores,
        penalty=10.0,
    )

    selection = solution["selection"]

    assert len(selection) == 4
    assert all(
        bit in (0, 1)
        for bit in selection
    )

    assert 0.0 <= solution["probability"] <= 1.0

    assert isinstance(
        expectation,
        float
    )

    print()
    print(
        "Q-Care Evidence -> QUBO -> QAOA"
    )
    print(
        "Scores:",
        scores
    )
    print(
        "Expectation:",
        expectation
    )
    print(
        "Selection:",
        selection
    )
    print(
        "Probability:",
        solution["probability"]
    )
    print(
        "Cost:",
        solution["cost"]
    )
    print()
    print(
        "PASS - Evidence -> QUBO -> QAOA integration test passed."
    )


if __name__ == "__main__":
    test_evidence_to_qubo_to_qaoa()