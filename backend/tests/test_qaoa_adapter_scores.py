"""
Q-Care QAOA Adapter-Score Diagnostic

Checks whether QAOA parameter optimization can recover
the best evidence pair from adapter-generated scores.

This is an optimization test, not a medical test.
"""

from src.quantum.qaoa_optimizer import (
    calculate_cost,
    build_qaoa_circuit,
    evaluate_statevector_layers,
    search_qaoa_parameters,
    extract_best_solution,
)


def test_adapter_scores_qaoa():

    scores = [
        6.5,
        6.5,
        1.8,
        1.8,
    ]

    # ------------------------------------------------------
    # Classical optimum
    # ------------------------------------------------------

    classical_selection = (
        1, 1, 0, 0
    )

    classical_cost = calculate_cost(
        classical_selection,
        scores,
        maximum_selected=2,
        penalty=10.0,
    )

    print()
    print("Q-Care QAOA Adapter-Score Diagnostic")
    print("--------------------------------------")
    print("Scores:", scores)
    print(
        "Expected classical selection:",
        classical_selection,
    )
    print(
        "Expected classical cost:",
        classical_cost,
    )

    # ------------------------------------------------------
    # QAOA parameter search
    # ------------------------------------------------------

    best = search_qaoa_parameters(
        scores,
        penalty=10.0,
    )

    print()
    print("Optimized gamma:", best["gamma"])
    print("Optimized beta:", best["beta"])
    print(
        "Optimized expectation:",
        best["expectation"],
    )

    # ------------------------------------------------------
    # Evaluate optimized circuit
    # ------------------------------------------------------

    circuit = build_qaoa_circuit(
        scores,
        penalty=10.0,
        p=1,
    )

    statevector = (
        evaluate_statevector_layers(
            circuit,
            [best["gamma"]],
            [best["beta"]],
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
    # Validation
    # ------------------------------------------------------

    assert solution["selection"] == classical_selection

    print()
    print(
        "PASS — QAOA recovered the classical optimum."
    )


if __name__ == "__main__":
    test_adapter_scores_qaoa()