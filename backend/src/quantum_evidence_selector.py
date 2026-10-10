"""
Q-Care Quantum Evidence Selector V1

Connects:

    Fused Evidence
        ↓
    Evidence → QUBO Adapter
        ↓
    QAOA Optimization
        ↓
    Selected Evidence

IMPORTANT:
This module performs evidence-selection optimization.

It does NOT:
- diagnose disease
- estimate disease probability
- determine medical severity
- replace clinical judgment
"""

from typing import Any, Dict, List

from src.evidence_to_qubo import build_qubo_input

from src.quantum.qaoa_optimizer import (
    build_qaoa_circuit,
    evaluate_statevector_layers,
    search_qaoa_parameters,
    extract_best_solution,
)


def select_evidence_with_qaoa(
    fused_evidence: Dict[str, Any],
    penalty: float = 10.0,
    p: int = 1,
) -> Dict[str, Any]:
    """
    Select the strongest evidence items using QAOA.

    Returns both the optimization result and the actual
    evidence records corresponding to selected QAOA bits.
    """

    # ------------------------------------------------------
    # STEP 1 — Evidence → QUBO
    # ------------------------------------------------------

    qubo_input = build_qubo_input(
        fused_evidence
    )

    if qubo_input["status"] != "qubo_ready":
        return {
            "status": "no_evidence",
            "selected_evidence": [],
            "selected_indices": [],
            "scores": [],
            "optimization": None,
            "qubo_input": qubo_input,
        }

    scores = qubo_input["scores"]

    if not scores:
        return {
            "status": "no_evidence",
            "selected_evidence": [],
            "selected_indices": [],
            "scores": [],
            "optimization": None,
            "qubo_input": qubo_input,
        }

    # ------------------------------------------------------
    # STEP 2 — QAOA circuit
    # ------------------------------------------------------

    circuit = build_qaoa_circuit(
        scores,
        penalty=penalty,
        p=p,
    )

    # ------------------------------------------------------
    # STEP 3 — Optimize QAOA parameters
    # ------------------------------------------------------

    if p == 1:

        optimized = search_qaoa_parameters(
            scores,
            penalty=penalty,
        )

        gammas = [
            optimized["gamma"]
        ]

        betas = [
            optimized["beta"]
        ]

    else:

        from src.quantum.qaoa_optimizer import (
            search_qaoa_parameters_layers,
        )

        optimized = (
            search_qaoa_parameters_layers(
                scores,
                penalty=penalty,
                p=p,
            )
        )

        gammas = optimized["gammas"]
        betas = optimized["betas"]

    # ------------------------------------------------------
    # STEP 4 — Evaluate optimized circuit
    # ------------------------------------------------------

    statevector = (
        evaluate_statevector_layers(
            circuit,
            gammas,
            betas,
        )
    )

    solution = extract_best_solution(
        statevector,
        scores,
        penalty=penalty,
    )

    selection = solution["selection"]

    # ------------------------------------------------------
    # STEP 5 — Map QAOA bits → evidence records
    # ------------------------------------------------------

    evidence_list = qubo_input["evidence"]

    selected_indices = [
        index
        for index, bit in enumerate(selection)
        if bit == 1
    ]

    selected_evidence = [
        evidence_list[index]
        for index in selected_indices
    ]

    # ------------------------------------------------------
    # STEP 6 — Build transparent result
    # ------------------------------------------------------

    return {
        "status": "selected",
        "selected_indices": selected_indices,
        "selected_evidence": selected_evidence,
        "scores": scores,
        "selection": selection,
        "optimization": {
            "depth": p,
            "gammas": gammas,
            "betas": betas,
            "expectation": optimized["expectation"],
            "probability": solution["probability"],
            "cost": solution["cost"],
        },
        "qubo_input": qubo_input,
    }