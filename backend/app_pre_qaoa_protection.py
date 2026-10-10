"""
Q-Care Backend API V8

Full assessment pipeline:

Text:
User input
    ↓
Safety Engine
    ↓
Clinical Context
    ↓
Evidence Retrieval
    ↓
V4 Evidence Ranking
    ↓
V5 Evidence Gate
    ↓
V8 Evidence Adapter
    ↓
V2.5 Evidence Fusion
    ↓
V2.6 Evidence Confidence
    ↓
Evidence → QUBO
    ↓
QAOA Evidence Selection
    ↓
V6 Precautionary Analysis
    ↓
Structured response

Image:
Uploaded image
    ↓
Gemini Vision
    ↓
Visual observations only
    ↓
Existing Q-Care V8 pipeline
    ↓
Precautionary analysis

IMPORTANT:
Q-Care does NOT diagnose medical conditions.
Gemini is used only for visual observation.
Quantum processing is used for evidence selection,
not diagnosis or medical severity.
"""

import os
import tempfile

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from src.safety_engine import check_safety
from src.clinical_context import classify_context
from src.evidence_engine import retrieve_evidence
from src.evidence_ranker_v4 import rank_retrieval_response
from src.evidence_gate import gate_ranked_response
from src.evidence_adapter import adapt_gate_to_fusion
from src.evidence_fusion import fuse_evidence
from src.evidence_confidence import calculate_confidence_profile
from src.quantum_evidence_selector import select_evidence_with_qaoa
from src.analysis_engine import analyze_assessment

from src.gemini_vision import (
    analyze_image_with_gemini,
    gemini_to_qcare_input,
)


app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


@app.route("/")
def home():
    frontend = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")
    return send_file(frontend)


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok",
        "service": "Q-Care Backend",
        "version": "V8",
        "image_vision": "google_gemini",
        "diagnostic": False,
    })


# =========================================================
# SHARED Q-CARE TEXT PIPELINE
# =========================================================

def run_qcare_pipeline(text):
    """
    Run the existing Q-Care V8 evidence and quantum pipeline.

    This function is shared by:
    - normal text assessments
    - image-derived visual observations

    It does NOT diagnose medical conditions.
    """

    # -----------------------------------------------------
    # 1. SAFETY
    # -----------------------------------------------------

    safety = check_safety(text)

    # -----------------------------------------------------
    # 2. CLINICAL CONTEXT
    # -----------------------------------------------------

    context = classify_context(text)

    query_context = context.get(
        "context",
        "unknown",
    )

    context_confidence = context.get(
        "confidence",
        0.0,
    )

    # -----------------------------------------------------
    # 3. EVIDENCE RETRIEVAL
    # -----------------------------------------------------

    retrieval = retrieve_evidence(
        text
    )

    # -----------------------------------------------------
    # 4. EVIDENCE RANKING
    # -----------------------------------------------------

    ranked = rank_retrieval_response(
        text,
        retrieval,
    )

    # -----------------------------------------------------
    # 5. EVIDENCE GATE
    # -----------------------------------------------------

    gated = gate_ranked_response(
        ranked
    )

    # -----------------------------------------------------
    # 6. ADAPT V5 → V2.5 FUSION
    # -----------------------------------------------------

    adapted_evidence = (
        adapt_gate_to_fusion(
            gated
        )
    )

    # -----------------------------------------------------
    # 7. EVIDENCE FUSION
    # -----------------------------------------------------

    fused = fuse_evidence(
        query=text,
        concepts=retrieval.get(
            "concepts",
            [],
        ),
        results=adapted_evidence,
        context={
            "clinical_context": query_context,
            "context_confidence": (
                context_confidence
            ),
        },
    )

    # -----------------------------------------------------
    # 8. EVIDENCE CONFIDENCE
    # -----------------------------------------------------

    confidence = (
        calculate_confidence_profile(
            fused
        )
    )

    # -----------------------------------------------------
    # 9. QUANTUM EVIDENCE SELECTION
    # -----------------------------------------------------

    quantum_selection = (
        select_evidence_with_qaoa(
            fused_evidence=fused,
            penalty=10.0,
            p=1,
        )
    )

    # -----------------------------------------------------
    # 10. PRECAUTIONARY ANALYSIS
    # -----------------------------------------------------

    analysis = analyze_assessment(
        safety=safety,
        evidence=gated,
        query_context=query_context,
        context_confidence=context_confidence,
    )

    # -----------------------------------------------------
    # RETURN PIPELINE
    # -----------------------------------------------------

    return {
        "safety": safety,

        "clinical_context": context,

        "retrieval": retrieval,

        "ranking": ranked,

        "evidence_gate": gated,

        "evidence_adapter": {
            "status": (
                "adapted"
                if adapted_evidence
                else "no_evidence"
            ),
            "adapted_count": len(
                adapted_evidence
            ),
        },

        "evidence_fusion": fused,

        "evidence_confidence": confidence,

        "quantum_evidence_selection": (
            quantum_selection
        ),

        "analysis": analysis,
    }


# =========================================================
# ASSESSMENT
# =========================================================

@app.route("/api/assess", methods=["POST"])
def assess():

    data = request.get_json(
        silent=True
    ) or {}

    text = data.get(
        "text",
        "",
    )

    # -----------------------------------------------------
    # INPUT VALIDATION
    # -----------------------------------------------------

    if not text or not isinstance(
        text,
        str,
    ):

        return jsonify({
            "status": "error",
            "message": (
                "Please provide a health description."
            ),
        }), 400

    text = text.strip()

    if not text:

        return jsonify({
            "status": "error",
            "message": (
                "Please provide a health description."
            ),
        }), 400

    # -----------------------------------------------------
    # RUN V8 PIPELINE
    # -----------------------------------------------------

    pipeline = run_qcare_pipeline(
        text
    )

    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

    return jsonify({

        "status": "success",

        "version": "V8",

        "query": text,

        "pipeline": pipeline,

        # Explicit safety boundary.
        "diagnostic": False,

        "quantum_role": (
            "QAOA is used experimentally "
            "to select a small set of relevant "
            "evidence sources. It does not "
            "diagnose disease or determine "
            "medical severity."
        ),

        "confidence_interpretation": (
            "The confidence value describes "
            "evidence quality and coverage, "
            "not disease probability or "
            "diagnostic certainty."
        ),

        "disclaimer": (
            "Q-Care provides precautionary "
            "health information and does not "
            "diagnose medical conditions."
        ),
    })


# =========================================================
# IMAGE ASSESSMENT
# =========================================================

@app.route("/api/assess-image", methods=["POST"])
def assess_image():

    # -----------------------------------------------------
    # INPUT VALIDATION
    # -----------------------------------------------------

    if "image" not in request.files:

        return jsonify({
            "status": "error",
            "message": (
                "Please provide an image using "
                "the 'image' upload field."
            ),
        }), 400

    uploaded_image = request.files["image"]

    if not uploaded_image.filename:

        return jsonify({
            "status": "error",
            "message": (
                "The uploaded image has no filename."
            ),
        }), 400

    # -----------------------------------------------------
    # IMAGE FORMAT
    # -----------------------------------------------------

    suffix = os.path.splitext(
        uploaded_image.filename
    )[1].lower()

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    if suffix not in allowed_extensions:

        return jsonify({
            "status": "error",
            "message": (
                "Unsupported image format. "
                "Use JPG, JPEG, PNG, or WEBP."
            ),
        }), 400

    temp_path = None

    try:

        # -------------------------------------------------
        # SAVE TEMPORARY IMAGE
        # -------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:

            uploaded_image.save(
                temp_file.name
            )

            temp_path = temp_file.name

        # -------------------------------------------------
        # 1. GEMINI VISUAL OBSERVATION
        # -------------------------------------------------

        gemini_result = (
            analyze_image_with_gemini(
                temp_path
            )
        )

        image_input = (
            gemini_to_qcare_input(
                gemini_result
            )
        )

        # -------------------------------------------------
        # GEMINI FAILURE / UNAVAILABLE
        # -------------------------------------------------

        if not image_input.get(
            "provider_available",
            False,
        ):

            return jsonify({

                "status": "partial",

                "version": "V8",

                "source": "image",

                "image_analysis": image_input,

                "diagnostic": False,

                "message": (
                    "Q-Care could not obtain visual "
                    "observations from Gemini. "
                    "No diagnosis was generated."
                ),

                "fallback": {
                    "available": True,
                    "action": (
                        "Use another available "
                        "input or retry when the "
                        "vision provider is available."
                    ),
                },

                "disclaimer": (
                    "Q-Care provides precautionary "
                    "health information and does not "
                    "diagnose medical conditions."
                ),
            })

        # -------------------------------------------------
        # 2. EXTRACT VISUAL OBSERVATIONS
        # -------------------------------------------------

        visual_text = image_input.get(
            "text",
            "",
        ).strip()

        if not visual_text:

            return jsonify({

                "status": "partial",

                "version": "V8",

                "source": "image",

                "image_analysis": image_input,

                "diagnostic": False,

                "message": (
                    "No usable visual observations "
                    "were returned from the image."
                ),

                "fallback": {
                    "available": True,
                    "action": (
                        "Use a clearer image or "
                        "provide a text description."
                    ),
                },

                "disclaimer": (
                    "Q-Care provides precautionary "
                    "health information and does not "
                    "diagnose medical conditions."
                ),
            })

        # -------------------------------------------------
        # 3. CONVERT OBSERVATIONS TO Q-CARE QUERY
        # -------------------------------------------------

        derived_query = (
            "Visual observations from an uploaded "
            "image: "
            + visual_text
        )

        # -------------------------------------------------
        # 4. RUN EXISTING V8 PIPELINE
        # -------------------------------------------------

        pipeline = run_qcare_pipeline(
            derived_query
        )

        # -------------------------------------------------
        # 5. FINAL IMAGE RESPONSE
        # -------------------------------------------------

        return jsonify({

            "status": "success",

            "version": "V8",

            "source": "image",

            "image_analysis": image_input,

            "derived_query": derived_query,

            "pipeline": pipeline,

            "diagnostic": False,

            "quantum_role": (
                "QAOA is used experimentally "
                "to select a small set of relevant "
                "evidence sources. It does not "
                "diagnose disease or determine "
                "medical severity."
            ),

            "confidence_interpretation": (
                "The confidence value describes "
                "evidence quality and coverage, "
                "not disease probability or "
                "diagnostic certainty."
            ),

            "disclaimer": (
                "Q-Care provides precautionary "
                "health information and does not "
                "diagnose medical conditions."
            ),
        })

    finally:

        # -------------------------------------------------
        # CLEAN TEMPORARY IMAGE
        # -------------------------------------------------

        if temp_path:

            try:

                os.remove(
                    temp_path
                )

            except OSError:

                pass


# =========================================================
# START SERVER
# =========================================================

@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({"status": "error", "message": "Image upload exceeds the 8 MB limit.", "diagnostic": False}), 413


@app.route("/api/health-card", methods=["POST"])
def health_card():
    """Create a non-diagnostic summary from an existing assessment."""
    data = request.get_json(silent=True) or {}
    result = data.get("assessment")
    if not isinstance(result, dict) or result.get("status") != "success":
        return jsonify({"status": "error", "message": "Provide a completed Q-Care assessment."}), 400
    pipeline = result.get("pipeline") or {}
    analysis = pipeline.get("analysis") or {}
    confidence = pipeline.get("evidence_confidence") or {}
    return jsonify({"status": "success", "health_card": {
        "source": result.get("source", "text"),
        "summary": analysis.get("summary") or ((analysis.get("recommendation") or {}).get("action") if isinstance(analysis.get("recommendation"), dict) else analysis.get("recommendation", "")),
        "priority": analysis.get("priority", "unknown"),
        "evidence_confidence": confidence,
        "confidence_interpretation": result.get("confidence_interpretation", "Evidence quality and coverage only; not disease probability."),
        "diagnostic": False,
        "disclaimer": result.get("disclaimer", "Q-Care provides precautionary health information and does not diagnose."),
    }})


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
