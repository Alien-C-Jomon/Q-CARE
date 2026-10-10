import time
import numpy as np

from src.quantum.qaoa_optimizer import (
    calculate_cost,
    build_qaoa_circuit,
    evaluate_statevector_layers,
    extract_best_solution,
    search_qaoa_parameters,
    search_qaoa_parameters_layers,
)


print("\n" + "=" * 100)
print("Q-CARE QAOA DEPTH BENCHMARK V3")
print("=" * 100)


# =========================================================
# Experimental evidence scores
# =========================================================

scores = [
    8.8,
    9.5,
    6.9,
    6.9,
]


# =========================================================
# Exact classical optimum
# =========================================================

def classical_optimum(scores):

    best = None

    number_of_candidates = len(scores)

    for state in range(2 ** number_of_candidates):

        selection = tuple(
            (state >> qubit) & 1
            for qubit in range(number_of_candidates)
        )

        cost = calculate_cost(
            selection,
            scores,
            maximum_selected=2,
            penalty=10.0,
        )

        if best is None or cost < best["cost"]:

            best = {
                "selection": selection,
                "cost": cost,
            }

    return best


classical = classical_optimum(scores)


print("\nCLASSICAL GROUND TRUTH")

print(
    "Selection:",
    classical["selection"]
)

print(
    "Cost:",
    classical["cost"]
)


# =========================================================
# Parameter grid
# =========================================================

gamma_values = np.linspace(
    0,
    2 * np.pi,
    21,
)

beta_values = np.linspace(
    0,
    np.pi,
    21,
)


# =========================================================
# Helper
# =========================================================

def optimal_state_probability(
    statevector,
    selection,
):
    """
    Return the probability of the classical optimal
    computational basis state.
    """

    state_index = sum(
        bit << qubit
        for qubit, bit in enumerate(selection)
    )

    return float(
        statevector.probabilities()[state_index]
    )


# =========================================================
# p=1
# =========================================================

print("\n" + "-" * 100)
print("QAOA DEPTH p=1")
print("-" * 100)


start = time.perf_counter()


p1 = search_qaoa_parameters(
    scores,
    penalty=10.0,
    gamma_values=gamma_values,
    beta_values=beta_values,
)


p1_circuit = build_qaoa_circuit(
    scores,
    penalty=10.0,
    p=1,
)


p1_statevector = evaluate_statevector_layers(
    p1_circuit,
    [p1["gamma"]],
    [p1["beta"]],
)


p1_solution = extract_best_solution(
    p1_statevector,
    scores,
    penalty=10.0,
)


p1_runtime = time.perf_counter() - start


p1_optimal_probability = (
    optimal_state_probability(
        p1_statevector,
        classical["selection"],
    )
)


print("Gamma:", round(p1["gamma"], 6))

print("Beta:", round(p1["beta"], 6))

print(
    "Expectation:",
    round(p1["expectation"], 6),
)

print(
    "Selection:",
    p1_solution["selection"],
)

print(
    "Cost:",
    p1_solution["cost"],
)

print(
    "Optimal probability:",
    round(
        p1_optimal_probability * 100,
        4,
    ),
    "%",
)

print(
    "Runtime:",
    round(
        p1_runtime * 1000,
        3,
    ),
    "ms",
)


# =========================================================
# p=2
# =========================================================

print("\n" + "-" * 100)
print("QAOA DEPTH p=2")
print("-" * 100)


start = time.perf_counter()


p2 = search_qaoa_parameters_layers(
    scores,
    penalty=10.0,
    p=2,
    gamma_values=gamma_values,
    beta_values=beta_values,
)


p2_circuit = build_qaoa_circuit(
    scores,
    penalty=10.0,
    p=2,
)


p2_statevector = evaluate_statevector_layers(
    p2_circuit,
    p2["gammas"],
    p2["betas"],
)


p2_solution = extract_best_solution(
    p2_statevector,
    scores,
    penalty=10.0,
)


p2_runtime = time.perf_counter() - start


p2_optimal_probability = (
    optimal_state_probability(
        p2_statevector,
        classical["selection"],
    )
)


print(
    "Gammas:",
    [
        round(value, 6)
        for value in p2["gammas"]
    ],
)

print(
    "Betas:",
    [
        round(value, 6)
        for value in p2["betas"]
    ],
)

print(
    "Expectation:",
    round(
        p2["expectation"],
        6,
    ),
)

print(
    "Selection:",
    p2_solution["selection"],
)

print(
    "Cost:",
    p2_solution["cost"],
)

print(
    "Optimal probability:",
    round(
        p2_optimal_probability * 100,
        4,
    ),
    "%",
)

print(
    "Runtime:",
    round(
        p2_runtime * 1000,
        3,
    ),
    "ms",
)


# =========================================================
# p=3
# =========================================================

print("\n" + "-" * 100)
print("QAOA DEPTH p=3")
print("-" * 100)


start = time.perf_counter()


p3 = search_qaoa_parameters_layers(
    scores,
    penalty=10.0,
    p=3,
    gamma_values=gamma_values,
    beta_values=beta_values,
)


p3_circuit = build_qaoa_circuit(
    scores,
    penalty=10.0,
    p=3,
)


p3_statevector = evaluate_statevector_layers(
    p3_circuit,
    p3["gammas"],
    p3["betas"],
)


p3_solution = extract_best_solution(
    p3_statevector,
    scores,
    penalty=10.0,
)


p3_runtime = time.perf_counter() - start


p3_optimal_probability = (
    optimal_state_probability(
        p3_statevector,
        classical["selection"],
    )
)


print(
    "Gammas:",
    [
        round(value, 6)
        for value in p3["gammas"]
    ],
)

print(
    "Betas:",
    [
        round(value, 6)
        for value in p3["betas"]
    ],
)

print(
    "Expectation:",
    round(
        p3["expectation"],
        6,
    ),
)

print(
    "Selection:",
    p3_solution["selection"],
)

print(
    "Cost:",
    p3_solution["cost"],
)

print(
    "Optimal probability:",
    round(
        p3_optimal_probability * 100,
        4,
    ),
    "%",
)

print(
    "Runtime:",
    round(
        p3_runtime * 1000,
        3,
    ),
    "ms",
)


# =========================================================
# Final comparison
# =========================================================

print("\n" + "=" * 100)
print("DEPTH COMPARISON")
print("=" * 100)


print(
    "\nDepth | Optimal Probability | "
    "Selected Cost | Matches Classical"
)

print("-" * 100)


p1_match = (
    p1_solution["selection"]
    == classical["selection"]
)

p2_match = (
    p2_solution["selection"]
    == classical["selection"]
)

p3_match = (
    p3_solution["selection"]
    == classical["selection"]
)


print(
    f"p=1   | "
    f"{p1_optimal_probability * 100:>17.4f}% | "
    f"{p1_solution['cost']:>13.3f} | "
    f"{'YES' if p1_match else 'NO'}"
)


print(
    f"p=2   | "
    f"{p2_optimal_probability * 100:>17.4f}% | "
    f"{p2_solution['cost']:>13.3f} | "
    f"{'YES' if p2_match else 'NO'}"
)


print(
    f"p=3   | "
    f"{p3_optimal_probability * 100:>17.4f}% | "
    f"{p3_solution['cost']:>13.3f} | "
    f"{'YES' if p3_match else 'NO'}"
)


print("\n" + "=" * 100)

print("INTERPRETATION")

print(
    "The classical optimizer provides the exact ground truth."
)

print(
    "QAOA depth is evaluated by solution quality, "
    "optimal-state probability, and cost."
)

print(
    "Higher QAOA depth does NOT automatically guarantee "
    "better performance."
)

print(
    "This experiment does NOT demonstrate quantum speedup."
)

print(
    "The evidence scores are synthetic optimization inputs, "
    "not medical measurements."
)

print("\n" + "=" * 100)
print("Q-CARE QAOA DEPTH BENCHMARK V3 COMPLETE")
print("=" * 100)