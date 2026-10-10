import time
import numpy as np

from src.quantum.qubo_model import build_candidates
from src.quantum.qaoa_optimizer import (
    search_qaoa_parameters,
    build_qaoa_circuit,
    evaluate_statevector,
    extract_best_solution,
    calculate_cost,
)


print("\n" + "=" * 90)
print("Q-CARE CLASSICAL vs QAOA BENCHMARK V1")
print("=" * 90)


# ---------------------------------------------------------
# Load candidates
# ---------------------------------------------------------

candidates = build_candidates()

scores = [
    candidate["score"]
    for candidate in candidates
]

print("\nEvidence candidates:")

for candidate in candidates:
    print(
        candidate["id"],
        "=",
        round(candidate["score"], 3)
    )


# ---------------------------------------------------------
# Classical exhaustive search
# ---------------------------------------------------------

print("\n" + "-" * 90)
print("CLASSICAL EXHAUSTIVE SEARCH")
print("-" * 90)

classical_start = time.perf_counter()

best_classical = None

for state in range(2 ** len(scores)):

    selection = tuple(
        (state >> qubit) & 1
        for qubit in range(len(scores))
    )

    cost = calculate_cost(
        selection,
        scores,
        maximum_selected=2,
        penalty=10.0,
    )

    if (
        best_classical is None
        or cost < best_classical["cost"]
    ):
        best_classical = {
            "selection": selection,
            "cost": cost,
        }

classical_time = (
    time.perf_counter()
    - classical_start
)

print(
    "Selection:",
    best_classical["selection"]
)

print(
    "Cost:",
    round(best_classical["cost"], 6)
)

print(
    "Runtime:",
    round(classical_time * 1000, 3),
    "ms"
)


# ---------------------------------------------------------
# QAOA optimization
# ---------------------------------------------------------

print("\n" + "-" * 90)
print("QAOA OPTIMIZATION")
print("-" * 90)

qaoa_start = time.perf_counter()

qaoa_result = search_qaoa_parameters(
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

qaoa_time = (
    time.perf_counter()
    - qaoa_start
)

print(
    "Gamma:",
    round(qaoa_result["gamma"], 6)
)

print(
    "Beta:",
    round(qaoa_result["beta"], 6)
)

print(
    "Expectation:",
    round(
        qaoa_result["expectation"],
        6,
    )
)

print(
    "Runtime:",
    round(qaoa_time * 1000, 3),
    "ms"
)


# ---------------------------------------------------------
# Generate optimized quantum state
# ---------------------------------------------------------

circuit = build_qaoa_circuit(
    scores,
    penalty=10.0,
    p=1,
)

statevector = evaluate_statevector(
    circuit,
    gamma=qaoa_result["gamma"],
    beta=qaoa_result["beta"],
)

qaoa_solution = extract_best_solution(
    statevector,
    scores,
    penalty=10.0,
)


# ---------------------------------------------------------
# QAOA result
# ---------------------------------------------------------

print("\n" + "-" * 90)
print("QAOA SOLUTION")
print("-" * 90)

print(
    "Selection:",
    qaoa_solution["selection"]
)

print(
    "Cost:",
    round(
        qaoa_solution["cost"],
        6,
    )
)

print(
    "Probability:",
    round(
        qaoa_solution["probability"],
        6,
    )
)


# ---------------------------------------------------------
# Comparison
# ---------------------------------------------------------

same_solution = (
    qaoa_solution["selection"]
    == best_classical["selection"]
)

same_cost = np.isclose(
    qaoa_solution["cost"],
    best_classical["cost"],
)


print("\n" + "-" * 90)
print("COMPARISON")
print("-" * 90)

print(
    "Same solution:",
    "YES" if same_solution else "NO"
)

print(
    "Same cost:",
    "YES" if same_cost else "NO"
)

print(
    "QAOA optimal probability:",
    f"{qaoa_solution['probability'] * 100:.2f}%"
)


# ---------------------------------------------------------
# Scientific guardrail
# ---------------------------------------------------------

print("\nIMPORTANT:")
print(
    "This benchmark does NOT claim quantum speedup."
)
print(
    "It measures solution quality and runtime "
    "for this experimental simulator setup."
)


# ---------------------------------------------------------
# Assertions
# ---------------------------------------------------------

assert best_classical["selection"] == (
    1,
    1,
    0,
    0,
)

assert np.isclose(
    best_classical["cost"],
    -18.3,
)

assert np.isfinite(
    qaoa_result["expectation"]
)

assert np.isfinite(
    qaoa_solution["cost"]
)

assert 0.0 <= qaoa_solution["probability"] <= 1.0


print("\n" + "=" * 90)
print("Q-CARE BENCHMARK V1 COMPLETE")
print("=" * 90)