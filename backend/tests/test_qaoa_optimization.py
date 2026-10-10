import numpy as np

from src.quantum.qubo_model import build_candidates
from src.quantum.qaoa_optimizer import (
    search_qaoa_parameters,
    evaluate_statevector,
    build_qaoa_circuit,
    extract_best_solution,
)


print("\n" + "=" * 90)
print("Q-CARE QAOA OPTIMIZATION V1")
print("=" * 90)


# ---------------------------------------------------------
# Load evidence candidates
# ---------------------------------------------------------

candidates = build_candidates()

scores = [
    candidate["score"]
    for candidate in candidates
]

print("\nEvidence scores:")

for candidate in candidates:
    print(
        candidate["id"],
        "=",
        round(candidate["score"], 3)
    )


# ---------------------------------------------------------
# Classical ground truth
# ---------------------------------------------------------

classical_selection = (1, 1, 0, 0)

print("\nClassical optimum:")
print("Selection:", classical_selection)
print("Evidence:", ["A", "B"])


# ---------------------------------------------------------
# QAOA parameter optimization
# ---------------------------------------------------------

print("\nSearching QAOA parameters...")

result = search_qaoa_parameters(
    scores,
    penalty=10.0,
    gamma_values=np.linspace(
        0,
        2 * np.pi,
        31,
    ),
    beta_values=np.linspace(
        0,
        np.pi,
        31,
    ),
)

print("\nBest QAOA parameters:")
print(
    "Gamma:",
    round(result["gamma"], 6)
)

print(
    "Beta:",
    round(result["beta"], 6)
)

print(
    "Expectation:",
    round(result["expectation"], 6)
)


# ---------------------------------------------------------
# Build optimized quantum state
# ---------------------------------------------------------

circuit = build_qaoa_circuit(
    scores,
    penalty=10.0,
    p=1,
)

statevector = evaluate_statevector(
    circuit,
    gamma=result["gamma"],
    beta=result["beta"],
)


# ---------------------------------------------------------
# Extract most probable solution
# ---------------------------------------------------------

solution = extract_best_solution(
    statevector,
    scores,
    penalty=10.0,
)

print("\nQAOA solution:")
print(
    "Selection:",
    solution["selection"]
)

print(
    "Probability:",
    round(
        solution["probability"],
        6,
    )
)

print(
    "Cost:",
    round(
        solution["cost"],
        6,
    )
)


# ---------------------------------------------------------
# Compare against classical optimum
# ---------------------------------------------------------

print("\nComparison:")

if solution["selection"] == classical_selection:
    print(
        "SUCCESS — QAOA recovered the classical optimum."
    )
else:
    print(
        "QAOA did not recover the classical optimum "
        "at p=1."
    )


# ---------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------

assert np.isfinite(
    result["expectation"]
)

assert np.isfinite(
    solution["probability"]
)

assert 0.0 <= solution["probability"] <= 1.0

assert np.isfinite(
    solution["cost"]
)


print("\n" + "=" * 90)
print("Q-CARE QAOA OPTIMIZATION TEST COMPLETE")
print("=" * 90)