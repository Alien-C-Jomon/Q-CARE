"""
Q-Care Evidence Engine
=======================

Retrieves candidate evidence from trusted public-health and
clinical-information sources.

Important:
    This module retrieves and organizes evidence.
    It does NOT diagnose medical conditions.

Pipeline role:

    User query
        ↓
    Concept extraction
        ↓
    Clinical-context classification
        ↓
    Trusted-source retrieval
        ↓
    Evidence metadata
        ↓
    Downstream ranking / gate / fusion / quantum selection
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List

import requests


# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

MEDLINEPLUS_API_URL = (
    "https://wsearch.nlm.nih.gov/ws/query"
)

WHO_API_URL = (
    "https://ghoapi.azureedge.net/api/Indicator"
)

CDC_API_URL = (
    "https://tools.cdc.gov/api/v2/resources/media"
)

REQUEST_TIMEOUT = 10


SOURCE_TIERS = {
    "World Health Organization": 1,
    "National Library of Medicine / MedlinePlus": 1,
    "Centers for Disease Control and Prevention": 1,
    "Verified Health & Care Web Search": 1,
}


# ---------------------------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------------------------

def _clean_text(value: Any) -> str:
    """
    Convert a value into clean text.

    Also removes common HTML/XML markup returned by
    MedlinePlus search results.
    """

    if value is None:
        return ""

    text = str(value)

    text = html.unescape(text)

    # Remove HTML tags.
    text = re.sub(r"<[^>]+>", " ", text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _get_json(
    url: str,
    params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Perform a GET request expecting JSON.

    This helper is intentionally defensive because official
    APIs can return different response structures or temporary
    failures.
    """

    try:
        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        return {
            "success": False,
            "access_status": "request_error",
            "status_code": None,
            "error": str(exc),
            "data": None,
        }

    if response.status_code != 200:
        return {
            "success": False,
            "access_status": "http_error",
            "status_code": response.status_code,
            "error": response.text[:500],
            "data": None,
        }

    try:
        data = response.json()
    except ValueError:
        return {
            "success": False,
            "access_status": "invalid_json",
            "status_code": response.status_code,
            "error": "Response was not valid JSON.",
            "data": None,
        }

    return {
        "success": True,
        "access_status": "success",
        "status_code": response.status_code,
        "error": None,
        "data": data,
    }


# ---------------------------------------------------------------------------
# QUERY NORMALIZATION
# ---------------------------------------------------------------------------

def build_evidence_query(text: Any) -> str:
    """
    Build a normalized search query from user input.

    The query is intentionally kept conservative.
    """

    if text is None:
        return ""

    query = str(text).strip()

    if not query:
        return ""

    query = re.sub(r"\s+", " ", query)

    return query


# ---------------------------------------------------------------------------
# CONCEPT EXTRACTION
# ---------------------------------------------------------------------------

CONCEPT_PATTERNS = {
    "fever": [
        r"\bfever\b",
        r"\btemperature\b",
        r"\bhigh temperature\b",
    ],

    "headache": [
        r"\bheadache\b",
        r"\bhead pain\b",
    ],

    "swelling": [
        r"\bswelling\b",
        r"\bswollen\b",
        r"\bswollen up\b",
    ],

    "eye": [
        r"\beye\b",
        r"\beyes\b",
        r"\beyelid\b",
        r"\beyelids\b",
    ],

    "breathing": [
        r"\bdifficulty breathing\b",
        r"\btrouble breathing\b",
        r"\bshortness of breath\b",
        r"\bbreathing difficulty\b",
        r"\bcan't breathe\b",
        r"\bcannot breathe\b",
    ],

    "chest pain": [
        r"\bchest pain\b",
        r"\bpain in my chest\b",
    ],

    "vomiting": [
        r"\bvomit\b",
        r"\bvomiting\b",
        r"\bthrowing up\b",
    ],

    "abdominal pain": [
        r"\babdominal pain\b",
        r"\bstomach pain\b",
        r"\bpain in my stomach\b",
    ],

    "vision": [
        r"\bvision\b",
        r"\bvisual\b",
        r"\bblurred vision\b",
        r"\bloss of vision\b",
        r"\bvision loss\b",
    ],

    "cough": [
        r"\bcough\b",
        r"\bcoughing\b",
    ],

    "sore throat": [
        r"\bsore throat\b",
        r"\bthroat pain\b",
    ],

    "diarrhea": [
        r"\bdiarrhea\b",
        r"\bloose stools\b",
    ],

    "rash": [
        r"\brash\b",
        r"\bskin rash\b",
    ],

    "dizziness": [
        r"\bdizziness\b",
        r"\bdizzy\b",
    ],

    "fatigue": [
        r"\bfatigue\b",
        r"\bvery tired\b",
        r"\btiredness\b",
    ],
}


def extract_concepts(text: Any) -> List[str]:
    """
    Extract recognized health concepts from a query.

    Example:

        "I have a fever and headache"

    returns:

        ["fever", "headache"]
    """

    query = build_evidence_query(text)

    if not query:
        return []

    lowered = query.lower()

    concepts: List[str] = []

    for concept, patterns in CONCEPT_PATTERNS.items():

        for pattern in patterns:

            if re.search(pattern, lowered):
                concepts.append(concept)
                break

    return concepts


# ---------------------------------------------------------------------------
# CLINICAL CONTEXT
# ---------------------------------------------------------------------------

def classify_clinical_context(text: Any) -> Dict[str, Any]:
    """
    Classify the purpose/context of the query.

    This is NOT a medical diagnosis.

    Possible contexts:

        emergency
        vaccination
        population
        prevention
        individual_symptom
        general
    """

    query = build_evidence_query(text).lower()

    if not query:
        return {
            "context": "general",
            "confidence": 0.0,
            "matched_terms": [],
            "reason": "No query was provided.",
        }

    emergency_terms = [
        "difficulty breathing",
        "can't breathe",
        "cannot breathe",
        "severe chest pain",
        "unconscious",
        "fainted",
        "seizure",
        "heavy bleeding",
        "severe bleeding",
        "stroke",
    ]

    vaccination_terms = [
        "vaccination",
        "vaccine",
        "vaccines",
        "immunization",
        "immunisation",
        "vaccine coverage",
    ]

    population_terms = [
        "number of cases",
        "reported cases",
        "incidence",
        "prevalence",
        "population",
        "statistics",
        "statistic",
        "coverage",
        "rate",
        "outbreak",
        "surveillance",
    ]

    prevention_terms = [
        "prevent",
        "prevention",
        "how can i avoid",
        "avoid getting",
        "reduce risk",
    ]

    individual_terms = [
        "i have",
        "i'm having",
        "im having",
        "my ",
        "me ",
        "i feel",
        "i am feeling",
        "symptom",
        "symptoms",
    ]

    def matches(terms: List[str]) -> List[str]:
        return [
            term
            for term in terms
            if term in query
        ]

    matched = matches(emergency_terms)

    if matched:
        return {
            "context": "emergency",
            "confidence": 1.0,
            "matched_terms": matched,
            "reason": (
                "The query contains an immediate safety-related "
                "signal and should be handled cautiously."
            ),
        }

    matched = matches(vaccination_terms)

    if matched:
        return {
            "context": "vaccination",
            "confidence": 0.95,
            "matched_terms": matched,
            "reason": (
                "The request concerns vaccination or immunization "
                "information."
            ),
        }

    matched = matches(population_terms)

    if matched:
        return {
            "context": "population",
            "confidence": 0.95,
            "matched_terms": matched,
            "reason": (
                "The request appears to concern population-level "
                "statistics, surveillance, or coverage."
            ),
        }

    matched = matches(prevention_terms)

    if matched:
        return {
            "context": "prevention",
            "confidence": 0.90,
            "matched_terms": matched,
            "reason": (
                "The request concerns prevention or reducing "
                "health risk."
            ),
        }

    matched = matches(individual_terms)

    if matched or extract_concepts(query):
        if not matched:
            matched = extract_concepts(query)

        return {
            "context": "individual_symptom",
            "confidence": 0.95,
            "matched_terms": matched,
            "reason": (
                "The query describes an individual's reported "
                "symptoms or health concern."
            ),
        }

    return {
        "context": "general",
        "confidence": 0.50,
        "matched_terms": [],
        "reason": (
            "The purpose of the query could not be classified "
            "more specifically."
        ),
    }


# ---------------------------------------------------------------------------
# PUBLIC-HEALTH QUERY DETECTION
# ---------------------------------------------------------------------------

def is_public_health_query(text: str) -> bool:
    """
    Return True when the query explicitly asks for
    population/public-health information.
    """

    context = classify_clinical_context(text)

    return context["context"] in {
        "population",
        "vaccination",
        "prevention",
    }


# ---------------------------------------------------------------------------
# MEDLINEPLUS API
# ---------------------------------------------------------------------------

def query_medlineplus_content(
    search_text: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Query the National Library of Medicine / MedlinePlus
    search service.

    MedlinePlus healthTopics search returns XML.

    This parser therefore uses ElementTree rather than
    treating the response as JSON.
    """

    query = build_evidence_query(search_text)

    if not query:
        return {
            "source": "National Library of Medicine / MedlinePlus",
            "status": "invalid_input",
            "results": [],
        }

    params = {
        "db": "healthTopics",
        "term": query,
        "retmax": limit,
        "rettype": "brief",
        "tool": "Q-Care",
    }

    try:
        response = requests.get(
            MEDLINEPLUS_API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        return {
            "source": "National Library of Medicine / MedlinePlus",
            "status": "request_error",
            "results": [],
            "error": str(exc),
        }

    if response.status_code != 200:
        return {
            "source": "National Library of Medicine / MedlinePlus",
            "status": "http_error",
            "status_code": response.status_code,
            "results": [],
        }

    try:
        root = ET.fromstring(response.text)
    except ET.ParseError as exc:
        return {
            "source": "National Library of Medicine / MedlinePlus",
            "status": "parse_error",
            "status_code": response.status_code,
            "results": [],
            "error": str(exc),
        }

    results: List[Dict[str, Any]] = []

    for document in root.findall(".//document"):

        if len(results) >= limit:
            break

        title = ""
        summary = ""

        for content in document.findall("content"):

            name = content.get("name", "")
            raw_value = "".join(content.itertext())

            value = _clean_text(raw_value)

            if name == "title":
                title = value

            elif name == "FullSummary":
                summary = value

        url = document.get("url")

        if not title:
            continue

        results.append({
            "title": title,
            "topic": title,
            "url": url,
            "summary": summary,
            "evidence_type": "clinical_information",
            "evidence_context": "individual",
        })

    return {
        "source": "National Library of Medicine / MedlinePlus",
        "status": "success",
        "status_code": response.status_code,
        "results": results,
    }


# ---------------------------------------------------------------------------
# WHO API
# ---------------------------------------------------------------------------

def query_who_indicators(
    search_text: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Query the official WHO GHO Indicator API.

    WHO indicators are treated as population/public-health
    evidence by default.

    They must NOT be interpreted as individual clinical
    evidence merely because an indicator contains words
    such as "patient" or "fever".
    """

    query = build_evidence_query(search_text)

    if not query:
        return {
            "source": "World Health Organization",
            "status": "invalid_input",
            "results": [],
        }

    # WHO indicators are appropriate mainly for explicit
    # public-health/statistical requests.
    context = classify_clinical_context(query)

    if context["context"] == "individual_symptom":
        return {
            "source": "World Health Organization",
            "status": "not_primary_for_individual_symptom",
            "status_code": None,
            "results": [],
        }

    safe_query = query.replace("'", "''")

    params = {
        "$filter": f"contains(IndicatorName,'{safe_query}')",
        "$top": limit,
        "$format": "json",
    }

    result = _get_json(
        WHO_API_URL,
        params=params,
    )

    if not result["success"]:
        return {
            "source": "World Health Organization",
            "status": result["access_status"],
            "status_code": result.get("status_code"),
            "results": [],
        }

    data = result.get("data")

    records = []

    if isinstance(data, dict):
        records = data.get("value", [])

    results: List[Dict[str, Any]] = []

    for record in records[:limit]:

        if not isinstance(record, dict):
            continue

        indicator_name = _clean_text(
            record.get("IndicatorName")
        )

        indicator_code = record.get(
            "IndicatorCode"
        )

        if not indicator_name:
            continue

        results.append({
            "title": indicator_name,
            "topic": indicator_name,
            "indicator_code": indicator_code,
            "indicator_name": indicator_name,
            "evidence_type": "public_health_statistic",
            "evidence_context": "population",
        })

    return {
        "source": "World Health Organization",
        "status": "success",
        "status_code": result.get("status_code"),
        "results": results,
    }


# ---------------------------------------------------------------------------
# CDC API
# ---------------------------------------------------------------------------

def query_cdc_content(
    search_text: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Query the official CDC Content Services API.

    This endpoint provides content/media search.

    It is not treated as a direct diagnostic or clinical
    decision-support source.
    """

    query = build_evidence_query(search_text)

    if not query:
        return {
            "source": "Centers for Disease Control and Prevention",
            "status": "invalid_input",
            "results": [],
        }

    params = {
        "q": query,
    }

    result = _get_json(
        CDC_API_URL,
        params=params,
    )

    if not result["success"]:
        return {
            "source": "Centers for Disease Control and Prevention",
            "status": result["access_status"],
            "status_code": result.get("status_code"),
            "results": [],
        }

    data = result.get("data")

    if isinstance(data, dict):

        records = (
            data.get("results")
            or data.get("data")
            or data.get("items")
            or data.get("results", [])
            or []
        )

    elif isinstance(data, list):

        records = data

    else:

        records = []

    results: List[Dict[str, Any]] = []

    for record in records[:limit]:

        if not isinstance(record, dict):
            continue

        title = (
            record.get("title")
            or record.get("name")
            or record.get("label")
        )

        url = (
            record.get("url")
            or record.get("link")
            or record.get("contentUrl")
        )

        title = _clean_text(title)

        if not title:
            continue

        results.append({
            "title": title,
            "topic": title,
            "url": url,
            "evidence_type": "clinical_information",
            "evidence_context": "individual",
        })

    return {
        "source": "Centers for Disease Control and Prevention",
        "status": "success",
        "status_code": result.get("status_code"),
        "results": results,
    }


# ---------------------------------------------------------------------------
# RESULT MERGING
# ---------------------------------------------------------------------------

def _merge_source_result(
    source_result: Dict[str, Any],
    output: List[Dict[str, Any]],
) -> None:
    """
    Add source metadata to each retrieved result.
    """

    source = source_result.get("source")

    if not source:
        return

    tier = SOURCE_TIERS.get(
        source,
        3,
    )

    for item in source_result.get("results", []):

        if not isinstance(item, dict):
            continue

        result = dict(item)

        result["source"] = source
        result["tier"] = tier

        output.append(result)


def _deduplicate_results(
    results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Remove duplicate evidence records.
    """

    seen = set()
    deduplicated = []

    for result in results:

        title = _clean_text(
            result.get("title")
            or result.get("topic")
            or result.get("indicator_name")
            or ""
        )

        source = str(
            result.get("source")
            or ""
        ).strip()

        key = (
            source.lower(),
            title.lower(),
        )

        if not title:
            continue

        if key in seen:
            continue

        seen.add(key)

        cleaned = dict(result)

        cleaned["title"] = title

        if cleaned.get("topic"):
            cleaned["topic"] = _clean_text(
                cleaned["topic"]
            )

        deduplicated.append(cleaned)

    return deduplicated


# ---------------------------------------------------------------------------
# SOURCE HEALTH CHECK
# ---------------------------------------------------------------------------

def check_trusted_sources() -> List[Dict[str, Any]]:
    """
    Check technical accessibility of official APIs.

    This does NOT determine medical trustworthiness and does
    NOT determine whether a source supports a conclusion.
    """

    checks: List[Dict[str, Any]] = []

    # WHO
    who_result = _get_json(
        WHO_API_URL,
        params={
            "$top": 1,
            "$format": "json",
        },
    )

    checks.append({
        "source": "World Health Organization",
        "endpoint": "WHO GHO OData API",
        "status_code": who_result.get("status_code"),
        "reachable": who_result.get("success", False),
        "access_status": who_result.get(
            "access_status"
        ),
    })

    # CDC
    cdc_result = _get_json(
        CDC_API_URL,
        params={
            "q": "health",
        },
    )

    checks.append({
        "source": "Centers for Disease Control and Prevention",
        "endpoint": "CDC Content Services API",
        "status_code": cdc_result.get("status_code"),
        "reachable": cdc_result.get("success", False),
        "access_status": cdc_result.get(
            "access_status"
        ),
    })

    # NIH
    checks.append({
        "source": "National Institutes of Health",
        "endpoint": None,
        "status_code": None,
        "reachable": False,
        "access_status": "api_not_configured",
    })

    # MedlinePlus
    try:

        response = requests.get(
            MEDLINEPLUS_API_URL,
            params={
                "db": "healthTopics",
                "term": "fever",
                "retmax": 1,
                "rettype": "brief",
                "tool": "Q-Care",
            },
            timeout=REQUEST_TIMEOUT,
        )

        medline_reachable = (
            response.status_code == 200
        )

        medline_status = (
            "success"
            if medline_reachable
            else "http_error"
        )

        medline_code = response.status_code

    except requests.RequestException:

        medline_reachable = False
        medline_status = "request_error"
        medline_code = None

    checks.append({
        "source": "National Library of Medicine / MedlinePlus",
        "endpoint": "MedlinePlus healthTopics search API",
        "status_code": medline_code,
        "reachable": medline_reachable,
        "access_status": medline_status,
    })

    return checks


# ---------------------------------------------------------------------------
# COMBINED RETRIEVAL
# ---------------------------------------------------------------------------

def retrieve_evidence(
    text: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Retrieve evidence for a user query.

    Individual symptom queries prioritize MedlinePlus.

    Population / vaccination / prevention queries can use
    WHO and CDC.

    The returned information is candidate evidence to be
    reviewed by downstream Q-Care components.

    It is NOT a diagnosis.
    """

def query_web_health_care(
    search_text: str,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Query real medical web search APIs for relevant health & care details.
    """
    import urllib.parse

    query = build_evidence_query(search_text)
    if not query:
        return {
            "source": "Verified Health & Care Web Search",
            "status": "invalid_input",
            "status_code": None,
            "results": [],
        }

    results: List[Dict[str, Any]] = []

    try:
        q = urllib.parse.quote(query + " medical health care")
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={q}&format=json"
        response = requests.get(
            url,
            headers={"User-Agent": "Q-Care-Health/1.0"},
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 200:
            data = response.json()
            search_items = data.get("query", {}).get("search", [])

            for item in search_items[:limit]:
                title = _clean_text(item.get("title"))
                snippet = _clean_text(item.get("snippet"))

                if title and snippet:
                    wiki_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                    results.append({
                        "title": f"{title} (Medical Care & Guidelines)",
                        "topic": title,
                        "url": wiki_url,
                        "summary": snippet,
                        "evidence_type": "clinical_information",
                        "evidence_context": "individual",
                    })
    except Exception:
        pass

    return {
        "source": "Verified Health & Care Web Search",
        "status": "success" if results else "no_results",
        "status_code": 200,
        "results": results,
    }


def retrieve_evidence(
    text: Any,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Retrieve evidence for a query from MedlinePlus, WHO, CDC, and Web Health Search.
    """

    query = build_evidence_query(text)

    if not query:
        return {
            "query": "",
            "concepts": [],
            "status": "invalid_input",
            "sources": [],
            "results": [],
        }

    concepts = extract_concepts(query)

    clinical_context = classify_clinical_context(
        query
    )

    source_results: List[Dict[str, Any]] = []

    # Always fetch web health & care details for QUBO ranking
    web_health = query_web_health_care(query, limit=limit)
    if web_health.get("results"):
        source_results.append(web_health)

    # -------------------------------------------------------
    # Individual symptom retrieval
    # -------------------------------------------------------

    if clinical_context["context"] == "individual_symptom":

        for concept in concepts:

            medline = query_medlineplus_content(
                concept,
                limit=limit,
            )

            source_results.append(
                medline
            )

        if not concepts:
            medline = query_medlineplus_content(
                query,
                limit=limit,
            )
            source_results.append(medline)

    # -------------------------------------------------------
    # Emergency queries
    # -------------------------------------------------------

    elif clinical_context["context"] == "emergency":

        for concept in concepts:

            medline = query_medlineplus_content(
                concept,
                limit=limit,
            )

            source_results.append(
                medline
            )

        if not concepts:

            cdc = query_cdc_content(
                query,
                limit=limit,
            )

            source_results.append(
                cdc
            )

    # -------------------------------------------------------
    # Vaccination queries
    # -------------------------------------------------------

    elif clinical_context["context"] == "vaccination":

        who = query_who_indicators(
            query,
            limit=limit,
        )

        source_results.append(
            who
        )

        cdc = query_cdc_content(
            query,
            limit=limit,
        )

        source_results.append(
            cdc
        )

    # -------------------------------------------------------
    # Population queries
    # -------------------------------------------------------

    elif clinical_context["context"] == "population":

        who = query_who_indicators(
            query,
            limit=limit,
        )

        source_results.append(
            who
        )

        cdc = query_cdc_content(
            query,
            limit=limit,
        )

        source_results.append(
            cdc
        )

    # -------------------------------------------------------
    # Prevention queries
    # -------------------------------------------------------

    elif clinical_context["context"] == "prevention":

        who = query_who_indicators(
            query,
            limit=limit,
        )

        source_results.append(
            who
        )

        cdc = query_cdc_content(
            query,
            limit=limit,
        )

        source_results.append(
            cdc
        )

        for concept in concepts:

            medline = query_medlineplus_content(
                concept,
                limit=limit,
            )

            source_results.append(
                medline
            )

    # -------------------------------------------------------
    # General query
    # -------------------------------------------------------

    else:

        if concepts:

            for concept in concepts:

                medline = query_medlineplus_content(
                    concept,
                    limit=limit,
                )

                source_results.append(
                    medline
                )

        else:

            medline = query_medlineplus_content(
                query,
                limit=limit,
            )

            source_results.append(
                medline
            )

    # -------------------------------------------------------
    # Flatten and deduplicate
    # -------------------------------------------------------

    flattened: List[Dict[str, Any]] = []

    for source_result in source_results:

        _merge_source_result(
            source_result,
            flattened,
        )

    flattened = _deduplicate_results(
        flattened
    )

    return {
        "query": query,
        "concepts": concepts,
        "context": clinical_context,
        "status": "completed",
        "sources": source_results,
        "results": flattened,
    }


# ---------------------------------------------------------------------------
# MODULE TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("Q-Care Evidence Engine")
    print("----------------------")

    test_query = "I have a fever and headache"

    print(
        "Query:",
        test_query,
    )

    print(
        "Concepts:",
        extract_concepts(test_query),
    )

    print(
        "Context:"
    )

    print(
        classify_clinical_context(
            test_query
        )
    )

    print(
        "\nRetrieving evidence..."
    )

    evidence = retrieve_evidence(
        test_query,
        limit=5,
    )

    print(
        "Status:",
        evidence["status"],
    )

    print(
        "Evidence count:",
        len(evidence["results"]),
    )

    for item in evidence["results"]:

        print(
            "-",
            item.get("source"),
            "|",
            item.get("title"),
        )