"""
Q-Care Evidence Engine V2.1

Purpose:
    Improve trusted evidence retrieval by separating:
    - individual health topics
    - population health
    - vaccination
    - prevention

This module retrieves evidence only.
It does NOT diagnose diseases.
"""

import re
import requests

from src.clinical_context import classify_context


REQUEST_TIMEOUT = 12


WHO_TOPIC_MAP = {
    "malaria": "https://www.who.int/health-topics/malaria",
    "dengue": "https://www.who.int/health-topics/dengue-and-severe-dengue",
    "measles": "https://www.who.int/health-topics/measles",
    "yellow fever": "https://www.who.int/health-topics/yellow-fever",
    "tuberculosis": "https://www.who.int/health-topics/tuberculosis",
    "influenza": "https://www.who.int/health-topics/influenza-seasonal",
    "flu": "https://www.who.int/health-topics/influenza-seasonal",
    "headache": "https://www.who.int/news-room/fact-sheets/detail/headache-disorders",
    "migraine": "https://www.who.int/news-room/fact-sheets/detail/headache-disorders",
}


CDC_TOPIC_MAP = {
    "malaria": "https://www.cdc.gov/malaria/",
    "dengue": "https://www.cdc.gov/dengue/",
    "measles": "https://www.cdc.gov/measles/",
    "yellow fever": "https://www.cdc.gov/yellow-fever/",
    "tuberculosis": "https://www.cdc.gov/tb/",
    "influenza": "https://www.cdc.gov/flu/",
    "flu": "https://www.cdc.gov/flu/",
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


# More specific phrases must be checked before individual concepts.
SPECIAL_TOPICS = [
    "yellow fever",
    "rheumatic fever",
]


def normalize_text(text):
    """
    Normalize text and remove obvious contact information.
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
    Extract concepts while preventing specific disease phrases
    from being incorrectly split into generic concepts.
    """

    normalized = normalize_text(text).lower()

    concepts = []

    # Handle specific multi-word topics first.
    for topic in SPECIAL_TOPICS:
        if topic in normalized:
            concepts.append(topic)

    # Remove special phrases before generic matching.
    reduced = normalized

    for topic in SPECIAL_TOPICS:
        reduced = reduced.replace(topic, " ")

    for concept, terms in CONCEPT_GROUPS.items():

        for term in terms:

            if term in reduced:
                concepts.append(concept)
                break

    return sorted(set(concepts))


def extract_topics(text):
    """
    Identify topics for which trusted health-topic pages exist.
    """

    normalized = normalize_text(text).lower()

    topics = []

    for topic in sorted(
        set(WHO_TOPIC_MAP) | set(CDC_TOPIC_MAP),
        key=len,
        reverse=True,
    ):

        if topic in normalized:
            topics.append(topic)

    return sorted(set(topics), key=len, reverse=True)


def build_evidence_query(text):
    """
    Convert the raw request into a structured retrieval query.
    """

    cleaned = normalize_text(text)

    context = classify_context(cleaned)

    return {
        "text": cleaned,
        "context": context,
        "concepts": extract_concepts(cleaned),
        "topics": extract_topics(cleaned),
    }


def fetch_url(url):
    """
    Safely fetch a trusted public page.
    """

    try:

        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Q-Care/2.1 research retrieval client"
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


def retrieve_topic_evidence(query_data):
    """
    Retrieve trusted topic-level evidence.

    Only retrieves topics for which Q-Care has an explicit
    trusted-source mapping.
    """

    results = []
    sources = []

    for topic in query_data["topics"]:

        who_url = WHO_TOPIC_MAP.get(topic)

        if who_url:

            result = fetch_url(who_url)

            sources.append({
                "source": "World Health Organization",
                "status": result["status"],
                "status_code": result["status_code"],
            })

            if result["status"] == "success":

                results.append({
                    "source": "World Health Organization",
                    "title": topic.title(),
                    "url": who_url,
                    "topic": topic,
                    "evidence_type": "clinical_information",
                    "evidence_context": "individual",
                    "retrieval_status": "success",
                })

        cdc_url = CDC_TOPIC_MAP.get(topic)

        if cdc_url:

            result = fetch_url(cdc_url)

            sources.append({
                "source": "Centers for Disease Control and Prevention",
                "status": result["status"],
                "status_code": result["status_code"],
            })

            if result["status"] == "success":

                results.append({
                    "source": "Centers for Disease Control and Prevention",
                    "title": topic.title(),
                    "url": cdc_url,
                    "topic": topic,
                    "evidence_type": "clinical_information",
                    "evidence_context": "individual",
                    "retrieval_status": "success",
                })

    return {
        "results": results,
        "sources": sources,
    }


def retrieve_population_evidence(query_data):
    """
    Retrieve WHO GHO indicators only for population/vaccination
    contexts.

    Individual symptom questions do NOT use this endpoint.
    """

    context = query_data["context"]["context"]

    if context not in {
        "population_health",
        "vaccination",
    }:

        return {
            "results": [],
            "sources": [],
        }

    concepts = query_data["concepts"]

    if not concepts:

        return {
            "results": [],
            "sources": [],
        }

    # Do not use generic "fever" for a query such as
    # "yellow fever vaccination coverage".
    statistical_concepts = [
        concept
        for concept in concepts
        if concept not in SPECIAL_TOPICS
    ]

    if not statistical_concepts:

        return {
            "results": [],
            "sources": [],
        }

    query = " ".join(statistical_concepts)

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
                "User-Agent": "Q-Care/2.1 research retrieval client"
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
                "indicator_code": record.get("IndicatorCode"),
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


def retrieve_evidence_v21(text):
    """
    Main Q-Care Evidence Engine V2.1 entry point.
    """

    query_data = build_evidence_query(text)

    topic_data = retrieve_topic_evidence(query_data)

    population_data = retrieve_population_evidence(query_data)

    results = (
        topic_data["results"]
        + population_data["results"]
    )

    sources = (
        topic_data["sources"]
        + population_data["sources"]
    )

    if results:

        status = "completed"

    elif sources:

        status = "no_relevant_evidence"

    else:

        status = "no_sources"

    return {
        "query": query_data["text"],
        "context": query_data["context"],
        "concepts": query_data["concepts"],
        "topics": query_data["topics"],
        "results": results,
        "sources": sources,
        "status": status,
    }