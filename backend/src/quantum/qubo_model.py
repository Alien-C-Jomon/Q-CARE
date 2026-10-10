"""
Q-Care Quantum Problem V1
QUBO model for constrained evidence selection.

This is an experimental optimization model.

It does NOT diagnose disease or estimate medical probability.
"""


def calculate_evidence_score(
    relevance,
    coverage,
    source_quality,
    redundancy,
):
    """
    Calculate the experimental evidence-selection score.

    This score is an engineering objective only.
    """

    return (
        0.4 * relevance
        + 0.3 * coverage
        + 0.3 * source_quality
        - 0.2 * redundancy
    )


def build_candidates():
    """
    Return the initial experimental evidence candidates.
    """

    candidates = [
        {
            "id": "A",
            "name": "WHO",
            "relevance": 9,
            "coverage": 8,
            "source_quality": 10,
            "redundancy": 1,
        },
        {
            "id": "B",
            "name": "MedlinePlus",
            "relevance": 10,
            "coverage": 9,
            "source_quality": 10,
            "redundancy": 1,
        },
        {
            "id": "C",
            "name": "Medical reference",
            "relevance": 7,
            "coverage": 7,
            "source_quality": 8,
            "redundancy": 2,
        },
        {
            "id": "D",
            "name": "Weak source",
            "relevance": 9,
            "coverage": 8,
            "source_quality": 3,
            "redundancy": 0,
        },
    ]

    for candidate in candidates:

        candidate["score"] = (
            calculate_evidence_score(
                candidate["relevance"],
                candidate["coverage"],
                candidate["source_quality"],
                candidate["redundancy"],
            )
        )

    return candidates


def calculate_qubo_cost(
    selected,
    scores,
    maximum_selected=2,
    penalty=10.0,
):
    """
    Calculate the QUBO-style cost.

    selected:
        List of binary values.

    scores:
        Candidate evidence scores.

    Lower cost is better.
    """

    if len(selected) != len(scores):
        raise ValueError(
            "selected and scores must have the same length"
        )

    reward = sum(
        score * bit
        for score, bit in zip(
            scores,
            selected,
        )
    )

    selected_count = sum(selected)

    constraint_penalty = penalty * (
        selected_count - maximum_selected
    ) ** 2

    return (
        -reward
        + constraint_penalty
    )


def find_classical_optimum(
    scores,
    maximum_selected=2,
    penalty=10.0,
):
    """
    Exhaustively search the small problem space.

    This is our classical ground-truth baseline.
    """

    import itertools

    best_cost = None
    best_selection = None

    for selected in itertools.product(
        [0, 1],
        repeat=len(scores),
    ):

        cost = calculate_qubo_cost(
            selected,
            scores,
            maximum_selected,
            penalty,
        )

        if (
            best_cost is None
            or cost < best_cost
        ):
            best_cost = cost
            best_selection = selected

    return {
        "selection": best_selection,
        "cost": best_cost,
    }