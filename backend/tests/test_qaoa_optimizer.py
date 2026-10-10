import numpy as np

from src.quantum.qubo_model import build_candidates
from src.quantum.qaoa_optimizer import (
    build_qaoa_circuit,
    calculate_cost,
    evaluate_statevector,
    calculate_expectation,
)


print("\n" + "=" * 90)
print("Q-CARE QUANTUM OPTIMIZER V1 — QAOA")
print("=" * 90)


# =========================================================
# PREPARE DATA
# =========================================================

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
        round(candidate["score"], 3),
    )


# =========================================================
# TEST 1 — QUBO COST
# =========================================================

optimal_selection = (
    1,
    1,
    0,
    0,
)

cost = calculate_cost(
    optimal_selection,
    scores,
)

print("\nTEST 1 — QUBO COST")

print(
    "A+B cost:",
    round(cost, 3),
)

assert cost == -18.3


# =========================================================
# TEST 2 — CIRCUIT CREATION
# =========================================================

circuit = build_qaoa_circuit(
    scores,
    penalty=10.0,
    p=1,
)

print("\nTEST 2 — CIRCUIT")

print(
    "Qubits:",
    circuit.num_qubits,
)

print(
    "Parameters:",
    circuit.parameters,
)

assert circuit.num_qubits == 4
assert len(circuit.parameters) == 2


# =========================================================
# TEST 3 — STATEVECTOR
# =========================================================

parameters = list(
    circuit.parameters
)

gamma = parameters[0]
beta = parameters[1]

statevector = evaluate_statevector(
    circuit,
    gamma=0.5,
    beta=0.3,
)

print("\nTEST 3 — STATEVECTOR")

print(
    "State dimension:",
    len(statevector),
)

assert len(statevector) == 16


# =========================================================
# TEST 4 — EXPECTATION VALUE
# =========================================================

expectation = calculate_expectation(
    statevector,
    scores,
)

print("\nTEST 4 — EXPECTATION")

print(
    "Expected QUBO cost:",
    round(expectation, 6),
)

assert np.isfinite(expectation)


# =========================================================
# FINAL
# =========================================================

print("\n" + "=" * 90)
print(
    "Q-CARE QAOA STRUCTURAL TESTS PASSED"
)
print("=" * 90)