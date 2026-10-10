"""
Q-CARE V2 Quantum Evidence Ranker

Experimental optimization layer.
It ranks/selects evidence; it does not diagnose disease.
"""

def classical_score(item):
    return (
        0.35 * item.get("relevance", 0.0)
        + 0.25 * item.get("reliability", 0.0)
        + 0.20 * item.get("freshness", 0.0)
        + 0.20 * item.get("coverage", 0.0)
        - 0.15 * item.get("contradiction", 0.0)
        - 0.10 * item.get("redundancy", 0.0)
    )


def rank_evidence(items, max_items=8):
    """
    Current V2 baseline.

    The quantum optimizer will replace/augment this selection
    once the evidence matrix is constructed.
    """
    ranked = []

    for index, item in enumerate(items):
        copy = dict(item)
        copy["id"] = str(copy.get("id", index))
        copy["classical_score"] = classical_score(copy)
        ranked.append(copy)

    ranked.sort(key=lambda x: x["classical_score"], reverse=True)

    return {
        "status": "classical_baseline",
        "selected": ranked[:max_items],
        "all_ranked": ranked,
    }
