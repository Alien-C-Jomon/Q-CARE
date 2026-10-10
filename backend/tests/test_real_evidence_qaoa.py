"""
Q-Care Real Evidence → QUBO → QAOA Integration Test V1

Uses the actual Q-Care evidence fusion layer and then sends
the resulting evidence into the QUBO/QAOA selection layer.

This is an evidence-selection experiment.
It does NOT diagnose medical conditions.
"""

from src.evidence_fusion import fuse_evidence
from src.evidence_to_qubo import build_qubo_input
from src.quantum.qaoa_optimizer import (
    calculate_cost,
    build_qaoa_circuit,
    evaluate_statevector_layers,
    search_qaoa_parameters,
    extract_best_solution,
)


def test_real_evidence_to_qaoa():

    # ------------------------------------------------------
    # Synthetic evidence records using the REAL fusion API
    # ------------------------------------------------------

    query = "I have a fever and headache"

    concepts = [
        "fever",
        "headache",
    ]

    results = [
        {
            "source": "World Health Organization",
            "title": "Fever information",
            "topic": "fever",
            "url": "https://www.who.int/",
            "source_tier": 1,
            "evidence_type": "clinical_information",
        },
        {
            "source": "National Library of Medicine / MedlinePlus",
            "title": "Headache information",
            "topic": "headache",
            "url": "https://medlineplus.gov/",
            "source_tier": 1,
            "evidence_type": "clinical_information",
        },
        {
            "source": "Centers for Disease Control and Prevention",
            "title": "General health information",
            "topic": "general",
            "url": "https://www.cdc.gov/",
            "source_tier": 1,
            "evidence_type": "clinical_information",
        },
        {
            "source": "Unknown source",
            "title": "General information",
            "topic": "general",
            "url": "https://example.com/",
            "source_tier": 3,
            "evidence_type": "unknown",
        },
    ]

    # ------------------------------------------------------
    # STEP 1 — REAL EVIDENCE FUSION
    # ------------------------------------------------------

    fused = fuse_evidence(
        query=query,
        concepts=concepts,
        results=results,
        context={
            "type": "individual"
        },
    )

    assert fused["evidence_count"] == 4

    print()
    print("Q-Care Real Evidence -> QUBO -> QAOA")
    print("------------------------------------")
    print(
        "Fused evidence count:",
        fused["evidence_count"],
    )

    # ------------------------------------------------------
    # STEP 2 — EVIDENCE → QUBO
    # ------------------------------------------------------

    qubo_input = build_qubo_input(
        fused
    )

    scores = qubo_input["scores"]

    assert qubo_input["status"] == "qubo_ready"
    assert len(scores) == 4

    print(
        "QUBO scores:",
        scores,
    )

    # ------------------------------------------------------
    # STEP 3 — CLASSICAL REFERENCE
    # ------------------------------------------------------

    best_classical = None

    for a in range(2):
        for b in range(2):
            for c in range(2):
                for d in range(2):

                    selection = (
                        a,
                        b,
                        c,
                        d,
                    )

                    cost = calculate_cost(
                        selection,
                        scores,
                        maximum_selected=2,
                        penalty=10.0,
                    )

                    if (
                        best_classical is None
                        or cost
                        < best_classical["cost"]
                    ):
                        best_classical = {
                            "selection": selection,
                            "cost": cost,
                        }

    print(
        "Classical optimum:",
        best_classical["selection"],
    )

    print(
        "Classical cost:",
        best_classical["cost"],
    )

    # ------------------------------------------------------
    # STEP 4 — QAOA PARAMETER OPTIMIZATION
    # ------------------------------------------------------

    best_parameters = (
        search_qaoa_parameters(
            scores,
            penalty=10.0,
        )
    )

    print()
    print(
        "Optimized gamma:",
        best_parameters["gamma"],
    )

    print(
        "Optimized beta:",
        best_parameters["beta"],
    )

    print(
        "Optimized expectation:",
        best_parameters["expectation"],
    )

    # ------------------------------------------------------
    # STEP 5 — EVALUATE OPTIMIZED CIRCUIT
    # ------------------------------------------------------

    circuit = build_qaoa_circuit(
        scores,
        penalty=10.0,
        p=1,
    )

    statevector = (
        evaluate_statevector_layers(
            circuit,
            [
                best_parameters["gamma"]
            ],
            [
                best_parameters["beta"]
            ],
        )
    )

    solution = extract_best_solution(
        statevector,
        scores,
        penalty=10.0,
    )

    print()
    print(
        "QAOA selection:",
        solution["selection"],
    )

    print(
        "QAOA probability:",
        solution["probability"],
    )

    print(
        "QAOA cost:",
        solution["cost"],
    )

    # ------------------------------------------------------
    # STEP 6 — VERIFY OPTIMUM
    # ------------------------------------------------------

    assert (
        solution["selection"]
        == best_classical["selection"]
    )

    assert (
        solution["cost"]
        == best_classical["cost"]
    )

    print()
    print(
        "PASS - Real evidence fusion -> QUBO -> QAOA passed."
    )


if __name__ == "__main__":
    test_real_evidence_to_qaoa()