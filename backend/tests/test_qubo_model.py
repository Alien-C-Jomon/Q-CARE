from src.quantum.qubo_model import (
    build_candidates,
    find_classical_optimum,
)


print("\n" + "=" * 90)
print("Q-CARE QUANTUM PROBLEM V1 — CLASSICAL QUBO BASELINE")
print("=" * 90)


candidates = build_candidates()

print("\nEVIDENCE CANDIDATES")

for candidate in candidates:

    print(
        candidate["id"],
        "-",
        candidate["name"],
        "score =",
        round(candidate["score"], 3),
    )


scores = [
    candidate["score"]
    for candidate in candidates
]


result = find_classical_optimum(
    scores=scores,
    maximum_selected=2,
    penalty=10.0,
)


print("\nCLASSICAL OPTIMUM")

print(
    "Selection:",
    result["selection"],
)

print(
    "Cost:",
    round(result["cost"], 3),
)


selected_candidates = [
    candidate["id"]
    for candidate, selected
    in zip(
        candidates,
        result["selection"],
    )
    if selected
]


print(
    "Selected evidence:",
    selected_candidates,
)


assert sum(
    result["selection"]
) <= 2

assert result["selection"] == (
    1,
    1,
    0,
    0,
)


print("\n" + "=" * 90)
print(
    "CLASSICAL QUBO BASELINE TEST PASSED"
)
print("=" * 90)