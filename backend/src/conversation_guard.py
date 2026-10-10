"""
Q-Care Conversation Guard

Validates untrusted Gemini wording against a Q-Care fact pack.

Gemini is never treated as an evidence source.
If validation fails or is uncertain, Q-Care's own
safe template is used instead.

This module does NOT diagnose medical conditions.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Sequence, Set
from urllib.parse import urlparse


APPROVED_SOURCE_NAMES = {
    "World Health Organization",
    "National Library of Medicine / MedlinePlus",
    "Centers for Disease Control and Prevention",
    "National Institutes of Health",
}

APPROVED_HOST_SUFFIXES = (
    "who.int",
    "medlineplus.gov",
    "cdc.gov",
    "nih.gov",
    "nlm.nih.gov",
    "ncbi.nlm.nih.gov",
)

UNAPPROVED_SOURCE_MARKERS = (
    "mayo clinic",
    "webmd",
    "healthline",
    "wikipedia",
    "reddit",
    "quora",
    "tiktok",
    "instagram",
    "facebook",
    "twitter",
    "youtube",
    "chatgpt",
    "blog",
    "news article",
)

DIAGNOSTIC_PATTERNS = (
    r"\byou have\b.{0,40}\b(cancer|diabetes|stroke|infection|disease|flu|covid|malaria|tumor)\b",
    r"\byou are diagnosed\b",
    r"\bdiagnosed with\b",
    r"\bthis (is|means) (a |an )?(diagnosis|disease|cancer|infection)\b",
    r"\byou definitely have\b",
    r"\bthe diagnosis is\b",
    r"\bmedical diagnosis\b",
)

PROBABILITY_PATTERNS = (
    r"\bdisease probability\b",
    r"\bprobability of (a |the )?(disease|diagnosis|cancer|infection)\b",
    r"\b\d{1,3}\s*%\s*(chance|probability|likely)\b",
    r"\bchance you have\b",
    r"\bdiagnostic certainty\b",
    r"\bconfidence (score )?(means|shows|proves) you\b",
    r"\blikely that you have\b",
)

QUANTUM_OVERCLAIM_PATTERNS = (
    r"\bquantum advantage\b",
    r"\bmore accurate because (of )?quantum\b",
    r"\bquantum (proves|diagnoses|confirms)\b",
)

URL_RE = re.compile(
    r"https?://[^\s)\]>'\"<>]+",
    re.IGNORECASE,
)

CONFIDENCE_INTERPRETATION = (
    "The confidence value describes evidence quality and coverage, "
    "not disease probability or diagnostic certainty."
)

QUANTUM_ROLE = (
    "QAOA is used experimentally to select a small set of relevant "
    "evidence sources. It does not diagnose disease or determine "
    "medical severity."
)

DISCLAIMER = (
    "Q-Care provides precautionary health information and does not "
    "diagnose medical conditions."
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _normalize_url(url: str) -> str:
    cleaned = _clean(url).rstrip(".,;:)")
    parsed = urlparse(cleaned)
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    return f"{host}{path}".lower()


def _host_is_approved(url: str) -> bool:
    parsed = urlparse(_clean(url).rstrip(".,;:)"))
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return any(
        host == suffix or host.endswith("." + suffix)
        for suffix in APPROVED_HOST_SUFFIXES
    )


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    return []


def _record_source_fields(item: Dict[str, Any]) -> Dict[str, str]:
    title = _clean(
        item.get("title")
        or item.get("topic")
        or item.get("indicator_name")
        or item.get("name")
        or ""
    )
    source = _clean(item.get("source") or "")
    url = _clean(item.get("url") or item.get("link") or "")
    return {
        "source": source,
        "title": title,
        "url": url,
    }


def _collect_pipeline_evidence(pipeline: Dict[str, Any]) -> List[Dict[str, str]]:
    quantum = pipeline.get("quantum_evidence_selection") or {}
    fused = pipeline.get("evidence_fusion") or {}
    gated = pipeline.get("evidence_gate") or {}

    records: List[Any] = []

    if quantum.get("status") == "selected":
        records = _as_list(quantum.get("selected_evidence"))
    elif quantum.get("status") == "selector_failed":
        records = _as_list(quantum.get("selected_evidence"))
        if not records:
            records = _as_list(fused.get("evidence"))
    else:
        records = _as_list(fused.get("evidence"))
        if not records:
            records = _as_list(gated.get("accepted"))

    collected: List[Dict[str, str]] = []
    seen: Set[str] = set()

    for item in records:
        if not isinstance(item, dict):
            continue
        fields = _record_source_fields(item)
        key = "|".join(
            [
                fields["source"].lower(),
                fields["title"].lower(),
                _normalize_url(fields["url"]),
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        collected.append(fields)

    return collected


def build_fact_pack(pipeline: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the only set of facts Gemini may talk about.

    Image observations, if present, stay labeled as observations.
    """

    if not isinstance(pipeline, dict):
        pipeline = {}

    safety = pipeline.get("safety") or {}
    analysis = pipeline.get("analysis") or {}
    confidence = pipeline.get("evidence_confidence") or {}
    quantum = pipeline.get("quantum_evidence_selection") or {}
    recommendation = analysis.get("recommendation") or {}

    evidence = _collect_pipeline_evidence(pipeline)

    allowed_urls = [
        item["url"]
        for item in evidence
        if item.get("url")
    ]
    allowed_titles = [
        item["title"]
        for item in evidence
        if item.get("title")
    ]
    allowed_sources = sorted(
        {
            item["source"]
            for item in evidence
            if item.get("source")
        }
        | {
            name
            for name in APPROVED_SOURCE_NAMES
            if any(
                item.get("source") == name
                for item in evidence
            )
        }
    )

    quantum_status = quantum.get("status", "unavailable")
    quantum_succeeded = quantum_status == "selected"

    action = ""
    if isinstance(recommendation, dict):
        action = _clean(recommendation.get("action"))
    elif isinstance(recommendation, str):
        action = _clean(recommendation)

    if not action:
        action = _clean(
            (analysis.get("safety") or {}).get("recommendation")
            or safety.get("action")
        )

    return {
        "safety": {
            "urgency": safety.get("urgency", "unknown"),
            "matched_signals": _as_list(safety.get("matched_signals")),
            "action": _clean(safety.get("action")),
        },
        "analysis_action": action,
        "recommendation_category": (
            recommendation.get("category")
            if isinstance(recommendation, dict)
            else ""
        ),
        "confidence": {
            "label": confidence.get("confidence_label", "unavailable"),
            "overall": confidence.get("overall_confidence"),
            "interpretation": confidence.get(
                "interpretation",
                CONFIDENCE_INTERPRETATION,
            ),
        },
        "quantum": {
            "status": quantum_status,
            "succeeded": quantum_succeeded,
            "experimental": True,
            "role": QUANTUM_ROLE,
        },
        "evidence": evidence,
        "allowed_urls": allowed_urls,
        "allowed_titles": allowed_titles,
        "allowed_source_names": allowed_sources,
        "disclaimer": analysis.get("disclaimer") or DISCLAIMER,
        "diagnostic": False,
    }


def render_safe_template(fact_pack: Dict[str, Any]) -> Dict[str, Any]:
    """Q-Care wording that does not depend on Gemini."""

    safety = fact_pack.get("safety") or {}
    confidence = fact_pack.get("confidence") or {}
    quantum = fact_pack.get("quantum") or {}
    evidence = _as_list(fact_pack.get("evidence"))

    lines: List[str] = []

    urgency = safety.get("urgency")
    if urgency == "urgent":
        lines.append(
            safety.get("action")
            or (
                "Seek urgent medical evaluation. If the situation "
                "appears life-threatening, contact local emergency services."
            )
        )
    elif urgency == "prompt":
        lines.append(
            safety.get("action")
            or (
                "Consider contacting a qualified healthcare professional "
                "if symptoms are worsening, severe, or persistent."
            )
        )
    else:
        action = _clean(fact_pack.get("analysis_action"))
        if action:
            lines.append(action)
        else:
            lines.append(
                "Q-Care does not have enough relevant verified evidence "
                "to provide specific guidance."
            )

    if evidence:
        lines.append("Verified sources Q-Care reviewed:")
        for item in evidence:
            label = item.get("title") or item.get("source") or "Verified source"
            source = item.get("source")
            url = item.get("url")
            piece = f"- {label}"
            if source:
                piece += f" ({source})"
            if url:
                piece += f" {url}"
            lines.append(piece)
    else:
        lines.append(
            "No sufficiently relevant verified evidence was available "
            "for this request."
        )

    lines.append(
        _clean(confidence.get("interpretation"))
        or CONFIDENCE_INTERPRETATION
    )

    if quantum.get("succeeded"):
        lines.append(QUANTUM_ROLE)
    else:
        lines.append(
            "Experimental QAOA evidence selection did not succeed for "
            "this request. Any listed sources come from Q-Care's gated "
            "evidence, not from a completed quantum selection."
        )

    lines.append(fact_pack.get("disclaimer") or DISCLAIMER)

    cited = [
        {
            "source": item.get("source", ""),
            "title": item.get("title", ""),
            "url": item.get("url", ""),
        }
        for item in evidence
    ]

    return {
        "message": "\n".join(lines),
        "cited_sources": cited,
        "source": "qcare_template",
        "diagnostic": False,
    }


def _text_has_pattern(text: str, patterns: Sequence[str]) -> Optional[str]:
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
            return pattern
    return None


def _extract_urls(text: str) -> List[str]:
    return [
        match.rstrip(".,;:)")
        for match in URL_RE.findall(text or "")
    ]


def validate_conversation_output(
    message: Any,
    cited_sources: Any,
    fact_pack: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate untrusted Gemini output.

    status:
      - passed: wording may be shown
      - failed: unsupported or unsafe claim
      - uncertain: parser/guard cannot be confident
    """

    reasons: List[str] = []
    status = "passed"

    if not isinstance(message, str) or not message.strip():
        return {
            "status": "uncertain",
            "passed": False,
            "reasons": ["empty_or_invalid_message"],
            "fallback": True,
            "diagnostic": False,
        }

    text = message.strip()
    lowered = text.lower()

    allowed_urls = {
        _normalize_url(url)
        for url in _as_list(fact_pack.get("allowed_urls"))
        if url
    }
    allowed_titles = {
        _clean(title).lower()
        for title in _as_list(fact_pack.get("allowed_titles"))
        if title
    }
    allowed_sources = {
        _clean(name).lower()
        for name in _as_list(fact_pack.get("allowed_source_names"))
        if name
    }
    allowed_sources.update(
        name.lower()
        for name in APPROVED_SOURCE_NAMES
        if name.lower() in {
            item.get("source", "").lower()
            for item in _as_list(fact_pack.get("evidence"))
        }
    )

    if _text_has_pattern(text, DIAGNOSTIC_PATTERNS):
        reasons.append("diagnostic_language")
        status = "failed"

    if _text_has_pattern(text, PROBABILITY_PATTERNS):
        reasons.append("evidence_confidence_as_disease_probability")
        status = "failed"

    if _text_has_pattern(text, QUANTUM_OVERCLAIM_PATTERNS):
        reasons.append("quantum_overclaim")
        status = "failed"

    for marker in UNAPPROVED_SOURCE_MARKERS:
        if marker in lowered:
            reasons.append(f"unapproved_source:{marker}")
            status = "failed"

    for url in _extract_urls(text):
        normalized = _normalize_url(url)
        if normalized not in allowed_urls:
            reasons.append("invented_citation_url")
            status = "failed"
        elif not _host_is_approved(url):
            reasons.append("unapproved_citation_host")
            status = "failed"

    if not isinstance(cited_sources, list):
        reasons.append("cited_sources_not_a_list")
        status = "uncertain" if status == "passed" else status
        cited_sources = []

    for citation in cited_sources:
        if not isinstance(citation, dict):
            reasons.append("invalid_citation_object")
            status = "failed"
            continue

        source = _clean(citation.get("source"))
        title = _clean(citation.get("title"))
        url = _clean(citation.get("url"))

        if source and source.lower() not in allowed_sources:
            reasons.append("invented_citation_source")
            status = "failed"

        if title and title.lower() not in allowed_titles:
            reasons.append("invented_citation_title")
            status = "failed"

        if url:
            if _normalize_url(url) not in allowed_urls:
                reasons.append("invented_citation_url")
                status = "failed"
            elif not _host_is_approved(url):
                reasons.append("unapproved_citation_host")
                status = "failed"

    safety = fact_pack.get("safety") or {}
    if safety.get("urgency") == "urgent":
        urgent_markers = (
            "urgent",
            "emergency",
            "emergency services",
            "life-threatening",
        )
        if not any(marker in lowered for marker in urgent_markers):
            reasons.append("emergency_guidance_omitted")
            status = "failed"

    if (
        "disease probability" in lowered
        or "not a diagnosis" not in lowered
        and "does not diagnose" not in lowered
        and status == "passed"
    ):
        # Missing disclaimer is treated as uncertain, not as a pass.
        reasons.append("missing_non_diagnostic_disclaimer")
        status = "uncertain"

    if status == "passed" and reasons:
        status = "uncertain"

    return {
        "status": status,
        "passed": status == "passed",
        "reasons": reasons,
        "fallback": status != "passed",
        "diagnostic": False,
    }


def apply_conversation_guard(
    gemini_result: Dict[str, Any],
    fact_pack: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Decide whether Gemini wording may be shown.

    Untrusted provider output is replaced by the Q-Care template
    whenever validation does not clearly pass.
    """

    template = render_safe_template(fact_pack)

    if not isinstance(gemini_result, dict):
        return {
            "source": "qcare_template",
            "validated": False,
            "validation_status": "uncertain",
            "message": template["message"],
            "cited_sources": template["cited_sources"],
            "guard": {
                "status": "uncertain",
                "passed": False,
                "reasons": ["invalid_provider_result"],
                "fallback": True,
                "diagnostic": False,
            },
            "diagnostic": False,
        }

    provider_status = gemini_result.get("status")
    if provider_status != "success":
        return {
            "source": "qcare_template",
            "validated": False,
            "validation_status": "uncertain",
            "message": template["message"],
            "cited_sources": template["cited_sources"],
            "guard": {
                "status": "uncertain",
                "passed": False,
                "reasons": [
                    gemini_result.get("error_code")
                    or "gemini_unavailable"
                ],
                "fallback": True,
                "diagnostic": False,
            },
            "provider_error_code": gemini_result.get("error_code"),
            "diagnostic": False,
        }

    guard = validate_conversation_output(
        gemini_result.get("message"),
        gemini_result.get("cited_sources"),
        fact_pack,
    )

    if not guard["passed"]:
        return {
            "source": "qcare_template",
            "validated": False,
            "validation_status": guard["status"],
            "message": template["message"],
            "cited_sources": template["cited_sources"],
            "guard": guard,
            "diagnostic": False,
        }

    return {
        "source": "gemini",
        "validated": True,
        "validation_status": "passed",
        "message": str(gemini_result.get("message", "")).strip(),
        "cited_sources": gemini_result.get("cited_sources") or [],
        "guard": guard,
        "diagnostic": False,
    }
