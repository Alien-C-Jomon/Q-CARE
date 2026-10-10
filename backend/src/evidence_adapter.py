"""
Q-Care Evidence Adapter V1

Adapts V4/V5 gated evidence into the structure
expected by Evidence Fusion V2.5.

IMPORTANT:
This adapter only transforms evidence metadata.
It does NOT diagnose conditions or estimate
medical probability/severity.
"""


def adapt_gate_to_fusion(gated_response):
    """
    Convert accepted V4/V5 evidence into the
    structure expected by Evidence Fusion.
    """

    if not isinstance(
        gated_response,
        dict,
    ):
        return []

    adapted = []

    for evidence in gated_response.get(
        "accepted",
        [],
    ):

        if not isinstance(
            evidence,
            dict,
        ):
            continue

        item = dict(
            evidence
        )

        relevance = item.get(
            "relevance",
            {},
        )

        if not isinstance(
            relevance,
            dict,
        ):
            relevance = {}

        # V4 stores these inside relevance.
        item["evidence_type"] = (
            relevance.get(
                "evidence_type",
                "unknown",
            )
        )

        item["evidence_context"] = (
            relevance.get(
                "context",
                "unknown",
            )
        )

        # Fusion uses topic/title for
        # conservative concept matching.
        if "topic" not in item:

            item["topic"] = (
                item.get("indicator_name")
                or item.get("title")
                or item.get("text")
                or item.get("content")
                or ""
            )

        if "title" not in item:

            item["title"] = (
                item.get("topic")
                or "Untitled evidence"
            )

        adapted.append(
            item
        )

    return adapted