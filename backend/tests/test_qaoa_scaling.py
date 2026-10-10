import time
import numpy as np

from src.quantum.qaoa_optimizer import (
    calculate_cost,
    search_qaoa_parameters,
    build_qaoa_circuit,
    evaluate_statevector,
    extract_best_solution,
)


print("\n" + "=" * 100)
print("Q-CARE QAOA SCALING BENCHMARK V2")
print("=" * 100)


# ---------------------------------------------------------
# Experimental problem sizes
# ---------------------------------------------------------

problem_sizes = [4, 6, 8, 10, 12]

# Keep the QAOA parameter grid smaller than V1.
# This keeps the scaling experiment practical.
gamma_values = np.linspace(
    0,
    2 * np.pi,
    11,
)

beta_values = np.linspace(
    0,
    np.pi,
    11,
)


# ---------------------------------------------------------
# Generate deterministic evidence scores
# ---------------------------------------------------------

def generate_scores(number_of_candidates):
    """
    Generate deterministic experimental scores.

    These are NOT medical measurements.
    They are only used to study optimizer scaling.
    """

    base_scores = [
        8.8,
        9.5,
        6.9,
        6.9,
        8.2,
        7.7,
        6.4,
        7.1,
        8.6,
        6.8,
        7.9,
        6.6,
    ]

    return base_scores[:number_of_candidates]


# ---------------------------------------------------------
# Classical exhaustive optimization
# ---------------------------------------------------------

def classical_optimize(scores):

    best = None

    number_of_candidates = len(scores)

    start = time.perf_counter()

    for state in range(
        2 ** number_of_candidates
    ):

        selection = tuple(
            (state >> qubit) & 1
            for qubit in range(
                number_of_candidates
            )
        )

        cost = calculate_cost(
            selection,
            scores,
            maximum_selected=2,
            penalty=10.0,
        )

        if (
            best is None
            or cost < best["cost"]
        ):
            best = {
                "selection": selection,
                "cost": cost,
            }

    runtime = (
        time.perf_counter()
        - start
    )

    best["runtime"] = runtime

    return best


# ---------------------------------------------------------
# QAOA optimization
# ---------------------------------------------------------

def qaoa_optimize(scores):

    start = time.perf_counter()

    result = search_qaoa_parameters(
        scores,
        penalty=10.0,
        gamma_values=gamma_values,
        beta_values=beta_values,
    )

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

    solution = extract_best_solution(
        statevector,
        scores,
        penalty=10.0,
    )

    runtime = (
        time.perf_counter()
        - start
    )

    return {
        "gamma": result["gamma"],
        "beta": result["beta"],
        "expectation": result["expectation"],
        "selection": solution["selection"],
        "cost": solution["cost"],
        "probability": solution["probability"],
        "runtime": runtime,
    }


# ---------------------------------------------------------
# Run benchmark
# ---------------------------------------------------------

results = []


for number_of_candidates in problem_sizes:

    scores = generate_scores(
        number_of_candidates
    )

    print("\n" + "-" * 100)

    print(
        f"PROBLEM SIZE: "
        f"{number_of_candidates} CANDIDATES"
    )

    print(
        f"State space: "
        f"2^{number_of_candidates} = "
        f"{2 ** number_of_candidates}"
    )

    # -----------------------------------------------------
    # Classical
    # -----------------------------------------------------

    classical = classical_optimize(
        scores
    )

    print("\nClassical:")
    print(
        "Selection:",
        classical["selection"]
    )
    print(
        "Cost:",
        round(
            classical["cost"],
            6,
        )
    )
    print(
        "Runtime:",
        round(
            classical["runtime"] * 1000,
            3,
        ),
        "ms",
    )

    # -----------------------------------------------------
    # QAOA
    # -----------------------------------------------------

    qaoa = qaoa_optimize(
        scores
    )

    print("\nQAOA:")
    print(
        "Gamma:",
        round(
            qaoa["gamma"],
            6,
        )
    )
    print(
        "Beta:",
        round(
            qaoa["beta"],
            6,
        )
    )
    print(
        "Expectation:",
        round(
            qaoa["expectation"],
            6,
        )
    )
    print(
        "Selection:",
        qaoa["selection"]
    )
    print(
        "Cost:",
        round(
            qaoa["cost"],
            6,
        )
    )
    print(
        "Probability:",
        round(
            qaoa["probability"],
            6,
        )
    )
    print(
        "Runtime:",
        round(
            qaoa["runtime"] * 1000,
            3,
        ),
        "ms",
    )

    # -----------------------------------------------------
    # Compare
    # -----------------------------------------------------

    same_solution = (
        qaoa["selection"]
        == classical["selection"]
    )

    same_cost = np.isclose(
        qaoa["cost"],
        classical["cost"],
    )

    print("\nComparison:")
    print(
        "Same solution:",
        "YES" if same_solution else "NO"
    )
    print(
        "Same cost:",
        "YES" if same_cost else "NO"
    )

    results.append({
        "candidates": number_of_candidates,
        "states": 2 ** number_of_candidates,
        "classical_runtime_ms":
            classical["runtime"] * 1000,
        "qaoa_runtime_ms":
            qaoa["runtime"] * 1000,
        "classical_cost":
            classical["cost"],
        "qaoa_cost":
            qaoa["cost"],
        "qaoa_probability":
            qaoa["probability"],
        "same_solution":
            same_solution,
        "same_cost":
            same_cost,
    })


# ---------------------------------------------------------
# Final summary
# ---------------------------------------------------------

print("\n" + "=" * 100)
print("Q-CARE SCALING SUMMARY")
print("=" * 100)

print(
    "\nCandidates | States | Classical ms | "
    "QAOA ms | QAOA Cost | Probability | Match"
)

print("-" * 100)

for result in results:

    print(
        f"{result['candidates']:>10} | "
        f"{result['states']:>6} | "
        f"{result['classical_runtime_ms']:>13.3f} | "
        f"{result['qaoa_runtime_ms']:>7.3f} | "
        f"{result['qaoa_cost']:>9.3f} | "
        f"{result['qaoa_probability'] * 100:>10.2f}% | "
        f"{'YES' if result['same_solution'] else 'NO'}"
    )


print("\nIMPORTANT:")
print(
    "This is a simulator-based scaling experiment."
)

print(
    "It does NOT demonstrate quantum speedup."
)

print(
    "The generated scores are experimental "
    "optimization inputs, not medical data."
)

print("\n" + "=" * 100)
print("Q-CARE QAOA SCALING BENCHMARK V2 COMPLETE")
print("=" * 100)