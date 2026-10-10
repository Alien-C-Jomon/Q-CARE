"""
Q-Care V8 Evidence Pipeline Integration Test

Pipeline:

V4-style ranked evidence
        ↓
Evidence Gate
        ↓
V4 → Fusion Adapter
        ↓
Evidence Fusion V2.5
        ↓
Evidence Confidence V2.6
        ↓
Evidence → QUBO
        ↓
QAOA Evidence Selection

IMPORTANT:
This test validates evidence selection architecture only.

It does NOT establish:
- diagnosis
- disease probability
- medical severity
- clinical effectiveness
- quantum speedup
"""

from src.evidence_gate import gate_ranked_response
from src.evidence_fusion import fuse_evidence
from src.evidence_confidence import calculate_confidence_profile
from src.evidence_to_qubo import build_qubo_input
from src.quantum_evidence_selector import select_evidence_with_qaoa


def adapt_gate_to_fusion(
    gated_response,
):
    """
    Convert V4/V5 accepted evidence into the
    structure expected by Evidence Fusion V2.5.
    """

    adapted = []

    for evidence in gated_response.get(
        "accepted",
        [],
    ):

        item = dict(
            evidence
        )

        relevance = item.get(
            "relevance",
            {},
        )

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

        # Fusion expects topic/title fields.
        # Preserve the original evidence text when
        # available without changing the source record.
        if "topic" not in item:
            item["topic"] = (
                item.get("indicator_name")
                or item.get("title")
                or item.get("text")
                or item.get("content")
                or ""
            )

        if "title" not in item:
            item["title"] = item["topic"]

        adapted.append(
            item
        )

    return adapted


def main():

    print()
    print("Q-Care V8 Evidence Pipeline")
    print("--------------------------------")

    # ------------------------------------------------------
    # Synthetic V4-shaped ranked evidence
    # ------------------------------------------------------

    ranked_response = {

        "query":
            "I have a fever and headache",

        "query_context":
            "individual_symptom",

        "context_confidence":
            0.95,

        "results": [

            {
                "source":
                    "World Health Organization",

                "tier":
                    1,

                "title":
                    "Fever information",

                "topic":
                    "fever",

                "relevance": {

                    "score":
                        90.0,

                    "matched_concepts":
                        [
                            "fever"
                        ],

                    "evidence_type":
                        "clinical_information",

                    "context":
                        "individual",
                },
            },

            {
                "source":
                    "National Library of Medicine / MedlinePlus",

                "tier":
                    1,

                "title":
                    "Headache information",

                "topic":
                    "headache",

                "relevance": {

                    "score":
                        88.0,

                    "matched_concepts":
                        [
                            "headache"
                        ],

                    "evidence_type":
                        "clinical_information",

                    "context":
                        "individual",
                },
            },

            {
                "source":
                    "Centers for Disease Control and Prevention",

                "tier":
                    1,

                "title":
                    "Fever statistics",

                "topic":
                    "fever cases population",

                "relevance": {

                    "score":
                        40.0,

                    "matched_concepts":
                        [
                            "fever"
                        ],

                    "evidence_type":
                        "epidemiological_data",

                    "context":
                        "population",
                },
            },

            {
                "source":
                    "Unknown source",

                "tier":
                    3,

                "title":
                    "General health article",

                "topic":
                    "general health",

                "relevance": {

                    "score":
                        20.0,

                    "matched_concepts":
                        [],

                    "evidence_type":
                        "unknown",

                    "context":
                        "unknown",
                },
            },
        ],
    }

    # ------------------------------------------------------
    # STEP 1 — Evidence Gate
    # ------------------------------------------------------

    gated = gate_ranked_response(
        ranked_response
    )

    print(
        "Gate status:",
        gated["status"],
    )

    print(
        "Accepted:",
        gated["accepted_count"],
    )

    print(
        "Rejected:",
        gated["rejected_count"],
    )

    assert (
        gated["accepted_count"]
        == 2
    )

    assert (
        gated["rejected_count"]
        == 2
    )

    # ------------------------------------------------------
    # STEP 2 — V4 → Fusion Adapter
    # ------------------------------------------------------

    fusion_input = adapt_gate_to_fusion(
        gated
    )

    assert (
        len(fusion_input)
        == 2
    )

    assert all(
        item["evidence_type"]
        == "clinical_information"
        for item in fusion_input
    )

    assert all(
        item["evidence_context"]
        == "individual"
        for item in fusion_input
    )

    # ------------------------------------------------------
    # STEP 3 — Evidence Fusion
    # ------------------------------------------------------

    fused = fuse_evidence(

        query=
            ranked_response["query"],

        concepts=[
            "fever",
            "headache",
        ],

        results=
            fusion_input,

        context={
            "query_context":
                ranked_response[
                    "query_context"
                ],

            "context_confidence":
                ranked_response[
                    "context_confidence"
                ],
        },
    )

    print(
        "Fused evidence:",
        fused["evidence_count"],
    )

    print(
        "Source count:",
        fused[
            "source_agreement"
        ]["source_count"],
    )

    print(
        "Coverage:",
        fused[
            "coverage"
        ]["coverage_ratio"],
    )

    assert (
        fused["evidence_count"]
        == 2
    )

    assert (
        fused[
            "source_agreement"
        ]["source_count"]
        == 2
    )

    assert (
        fused[
            "coverage"
        ]["coverage_ratio"]
        == 1.0
    )

    # ------------------------------------------------------
    # STEP 4 — Confidence
    # ------------------------------------------------------

    confidence = (
        calculate_confidence_profile(
            fused
        )
    )

    print(
        "Evidence confidence:",
        confidence[
            "overall_confidence"
        ],
    )

    print(
        "Confidence label:",
        confidence[
            "confidence_label"
        ],
    )

    assert (
        confidence[
            "overall_confidence"
        ]
        > 0.65
    )

    assert (
        confidence[
            "interpretation"
        ]
        == (
            "Evidence quality and coverage "
            "assessment; not a diagnosis or "
            "disease probability."
        )
    )

    # ------------------------------------------------------
    # STEP 5 — Evidence → QUBO
    # ------------------------------------------------------

    qubo_input = build_qubo_input(
        fused
    )

    print(
        "QUBO scores:",
        qubo_input["scores"],
    )

    assert (
        qubo_input["status"]
        == "qubo_ready"
    )

    assert (
        len(qubo_input["scores"])
        == 2
    )

    # ------------------------------------------------------
    # STEP 6 — QAOA
    # ------------------------------------------------------

    quantum_result = (
        select_evidence_with_qaoa(
            fused,
            p=1,
        )
    )

    print(
        "QAOA status:",
        quantum_result["status"],
    )

    print(
        "QAOA selection:",
        quantum_result["selection"],
    )

    print(
        "Selected indices:",
        quantum_result[
            "selected_indices"
        ],
    )

    print(
        "QAOA probability:",
        quantum_result[
            "optimization"
        ]["probability"],
    )

    # With only two accepted evidence records
    # and maximum_selected=2, both should be selected.
    assert (
        quantum_result[
            "selected_indices"
        ]
        == [0, 1]
    )

    assert (
        len(
            quantum_result[
                "selected_evidence"
            ]
        )
        == 2
    )

    # ------------------------------------------------------
    # STEP 7 — Verify actual evidence mapping
    # ------------------------------------------------------

    selected_titles = {

        evidence["title"]

        for evidence in
        quantum_result[
            "selected_evidence"
        ]
    }

    assert (
        selected_titles
        == {
            "Fever information",
            "Headache information",
        }
    )

    # ------------------------------------------------------
    # Safety assertions
    # ------------------------------------------------------

    assert (
        "diagnosis"
        not in quantum_result
    )

    print()
    print(
        "PASS — V8 evidence pipeline "
        "integration passed."
    )


if __name__ == "__main__":
    main()