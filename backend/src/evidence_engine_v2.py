"""
Q-Care Evidence Engine V2

Purpose:
    Retrieve structured evidence from trusted public-health sources.

Design principles:
    1. Trusted sources first.
    2. Clinical symptom questions should prefer clinical/topic resources.
    3. Population/statistical questions can use WHO GHO.
    4. Evidence is never treated as a diagnosis.
    5. Retrieval failure must be explicit.
"""

import re
import requests

from src.clinical_context import classify_context


REQUEST_TIMEOUT = 12


TRUSTED_SOURCES = [
    {
        "name": "World Health Organization",
        "tier": 1,
        "type": "public_health",
        "website": "https://www.who.int/",
    },
    {
        "name": "Centers for Disease Control and Prevention",
        "tier": 1,
        "type": "public_health",
        "website": "https://www.cdc.gov/",
    },
    {
        "name": "National Institutes of Health",
        "tier": 1,
        "type": "medical_research",
        "website": "https://www.nih.gov/",
    },
]


# WHO topic pages that are useful for health-topic evidence.
WHO_TOPIC_MAP = {
    "influenza": "https://www.who.int/health-topics/influenza-seasonal",
    "flu": "https://www.who.int/health-topics/influenza-seasonal",
    "malaria": "https://www.who.int/health-topics/malaria",
    "dengue": "https://www.who.int/health-topics/dengue-and-severe-dengue",
    "measles": "https://www.who.int/health-topics/measles",
    "yellow fever": "https://www.who.int/health-topics/yellow-fever",
    "tuberculosis": "https://www.who.int/health-topics/tuberculosis",
    "headache": "https://www.who.int/news-room/fact-sheets/detail/headache-disorders",
    "migraine": "https://www.who.int/news-room/fact-sheets/detail/headache-disorders",
    "eye": "https://www.who.int/health-topics/blindness-and-visual-impairment",
    "vision": "https://www.who.int/health-topics/blindness-and-visual-impairment",
}


CDC_TOPIC_MAP = {
    "influenza": "https://www.cdc.gov/flu/",
    "flu": "https://www.cdc.gov/flu/",
    "malaria": "https://www.cdc.gov/malaria/",
    "dengue": "https://www.cdc.gov/dengue/",
    "measles": "https://www.cdc.gov/measles/",
    "yellow fever": "https://www.cdc.gov/yellow-fever/",
    "tuberculosis": "https://www.cdc.gov/tb/",
}


CONCEPT_GROUPS = {
    "fever": [
        "fever",
        "high fever",
        "temperature",
    ],
    "headache": [
        "headache",
        "head pain",
        "migraine",
    ],
    "swelling": [
        "swelling",
        "swollen",
        "puffiness",
        "puffy",
    ],
    "eye": [
        "eye",
        "eyes",
        "eyelid",
        "eyelids",
    ],
    "breathing": [
        "difficulty breathing",
        "breathing difficulty",
        "shortness of breath",
        "can't breathe",
        "cannot breathe",
    ],
    "chest pain": [
        "chest pain",
    ],
    "vomiting": [
        "vomiting",
        "vomit",
    ],
    "abdominal pain": [
        "abdominal pain",
        "stomach pain",
    ],
    "vision": [
        "vision loss",
        "blurred vision",
        "vision",
    ],
}


def normalize_text(text):
    """
    Normalize user text while removing obvious contact information.
    """

    if not text or not isinstance(text, str):
        return ""

    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[redacted-email]",
        text,
    )

    text = re.sub(
        r"\b(?:\+?\d[\d\s().-]{7,}\d)\b",
        "[redacted-phone]",
        text,
    )

    return " ".join(text.split())


def extract_concepts(text):
    """
    Extract known health concepts from the query.

    This does not diagnose anything.
    It only identifies retrieval topics.
    """

    text_lower = normalize_text(text).lower()

    concepts = []

    for concept, terms in CONCEPT_GROUPS.items():
        for term in terms:
            if term in text_lower:
                concepts.append(concept)
                break

    return concepts


def extract_topic_terms(text):
    """
    Extract topic terms that map to trusted health-topic resources.
    """

    text_lower = normalize_text(text).lower()

    topics = []

    for topic in set(WHO_TOPIC_MAP) | set(CDC_TOPIC_MAP):
        if topic in text_lower:
            topics.append(topic)

    return sorted(set(topics))


def build_evidence_query(text):
    """
    Build a privacy-conscious retrieval query.
    """

    cleaned = normalize_text(text)

    context = classify_context(cleaned)

    concepts = extract_concepts(cleaned)
    topics = extract_topic_terms(cleaned)

    return {
        "text": cleaned,
        "context": context,
        "concepts": concepts,
        "topics": topics,
    }


def _fetch_page(url):
    """
    Fetch a trusted public page.

    This function retrieves the page only.
    It does not interpret medical meaning.
    """

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Q-Care/2.0 research retrieval client"
            },
        )

        if response.status_code != 200:
            return {
                "status": "unavailable",
                "status_code": response.status_code,
                "url": url,
            }

        return {
            "status": "success",
            "status_code": response.status_code,
            "url": url,
            "content": response.text,
        }

    except requests.Timeout:
        return {
            "status": "timeout",
            "status_code": None,
            "url": url,
        }

    except requests.RequestException:
        return {
            "status": "request_error",
            "status_code": None,
            "url": url,
        }


def _build_topic_result(source_name, topic, url):
    """
    Convert a trusted topic page into a structured evidence record.

    Q-Care intentionally does not generate a medical conclusion here.
    """

    return {
        "source": source_name,
        "title": topic.title(),
        "url": url,
        "evidence_type": "clinical_information",
        "evidence_context": "individual",
        "topic": topic,
        "retrieval_status": "success",
    }


def retrieve_topic_evidence(query_data):
    """
    Retrieve topic-level evidence from trusted sources.
    """

    results = []
    source_status = []

    topics = query_data["topics"]

    for topic in topics:

        who_url = WHO_TOPIC_MAP.get(topic)

        if who_url:
            fetched = _fetch_page(who_url)

            source_status.append({
                "source": "World Health Organization",
                "status": fetched["status"],
                "status_code": fetched["status_code"],
            })

            if fetched["status"] == "success":
                results.append(
                    _build_topic_result(
                        "World Health Organization",
                        topic,
                        who_url,
                    )
                )

        cdc_url = CDC_TOPIC_MAP.get(topic)

        if cdc_url:
            fetched = _fetch_page(cdc_url)

            source_status.append({
                "source": "Centers for Disease Control and Prevention",
                "status": fetched["status"],
                "status_code": fetched["status_code"],
            })

            if fetched["status"] == "success":
                results.append(
                    _build_topic_result(
                        "Centers for Disease Control and Prevention",
                        topic,
                        cdc_url,
                    )
                )

    return {
        "results": results,
        "sources": source_status,
    }


def retrieve_population_evidence(query_data):
    """
    Population/statistical evidence.

    WHO GHO remains appropriate for population-level questions,
    but it is intentionally separated from individual symptom evidence.
    """

    context = query_data["context"]

    if context["context"] not in {
        "population_health",
        "vaccination",
    }:
        return {
            "results": [],
            "sources": [],
        }

    query_terms = query_data["concepts"]

    if not query_terms:
        return {
            "results": [],
            "sources": [],
        }

    query = " ".join(query_terms)

    safe_query = query.replace("'", "''")

    url = "https://ghoapi.azureedge.net/api/Indicator"

    try:
        response = requests.get(
            url,
            params={
                "$filter": f"contains(IndicatorName,'{safe_query}')",
                "$format": "json",
            },
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Q-Care/2.0 research retrieval client"
            },
        )

        if response.status_code != 200:
            return {
                "results": [],
                "sources": [{
                    "source": "World Health Organization",
                    "status": "unavailable",
                    "status_code": response.status_code,
                }],
            }

        payload = response.json()

        records = payload.get("value", [])

        results = []

        for record in records[:10]:

            results.append({
                "source": "World Health Organization",
                "title": record.get(
                    "IndicatorName",
                    "WHO health indicator",
                ),
                "indicator_code": record.get(
                    "IndicatorCode"
                ),
                "evidence_type": "public_health_statistic",
                "evidence_context": "population",
                "topic": query,
                "retrieval_status": "success",
            })

        return {
            "results": results,
            "sources": [{
                "source": "World Health Organization",
                "status": "success",
                "status_code": response.status_code,
            }],
        }

    except requests.Timeout:
        return {
            "results": [],
            "sources": [{
                "source": "World Health Organization",
                "status": "timeout",
                "status_code": None,
            }],
        }

    except (requests.RequestException, ValueError):
        return {
            "results": [],
            "sources": [{
                "source": "World Health Organization",
                "status": "request_error",
                "status_code": None,
            }],
        }


def retrieve_evidence_v2(text):
    """
    Main Q-Care Evidence Engine V2 entry point.
    """

    query_data = build_evidence_query(text)

    topic_evidence = retrieve_topic_evidence(query_data)

    population_evidence = retrieve_population_evidence(query_data)

    results = (
        topic_evidence["results"]
        + population_evidence["results"]
    )

    sources = (
        topic_evidence["sources"]
        + population_evidence["sources"]
    )

    return {
        "query": query_data["text"],
        "context": query_data["context"],
        "concepts": query_data["concepts"],
        "topics": query_data["topics"],
        "results": results,
        "sources": sources,
        "status": "completed" if sources else "no_sources",
    }