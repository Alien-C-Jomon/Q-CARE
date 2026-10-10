from src.evidence_fusion import (
    fuse_evidence,
    fuse_retrieval_response,
)


print("\n" + "=" * 90)
print("Q-CARE EVIDENCE FUSION V2.5")
print("=" * 90)


# =========================================================
# TEST 1 — SINGLE SYMPTOM
# =========================================================

query = "I have a fever"

results = [
    {
        "source": (
            "National Library of Medicine / MedlinePlus"
        ),
        "title": "Fever",
        "topic": "fever",
        "evidence_type": "clinical_information",
        "evidence_context": "individual",
    }
]

fused = fuse_evidence(
    query=query,
    concepts=["fever"],
    results=results,
    context={
        "context": "individual_symptom",
        "confidence": 0.95,
    },
)

print("\nTEST 1 — SINGLE SYMPTOM")

print(
    "Status:",
    fused["status"],
)

print(
    "Evidence count:",
    fused["evidence_count"],
)

print(
    "Coverage:",
    fused["coverage"],
)

print(
    "Sources:",
    fused["source_agreement"],
)


assert fused["status"] == "evidence_fused"
assert fused["evidence_count"] == 1
assert fused["coverage"]["coverage_ratio"] == 1.0


# =========================================================
# TEST 2 — MULTIPLE SYMPTOMS
# =========================================================

query = "I have a fever and headache"

results = [
    {
        "source": (
            "National Library of Medicine / MedlinePlus"
        ),
        "title": "Fever",
        "topic": "fever",
        "evidence_type": "clinical_information",
        "evidence_context": "individual",
    },
    {
        "source": (
            "National Library of Medicine / MedlinePlus"
        ),
        "title": "Headache",
        "topic": "headache",
        "evidence_type": "clinical_information",
        "evidence_context": "individual",
    },
]

fused = fuse_evidence(
    query=query,
    concepts=[
        "fever",
        "headache",
    ],
    results=results,
    context={
        "context": "individual_symptom",
        "confidence": 0.95,
    },
)

print("\nTEST 2 — MULTIPLE SYMPTOMS")

print(
    "Status:",
    fused["status"],
)

print(
    "Evidence count:",
    fused["evidence_count"],
)

print(
    "Coverage:",
    fused["coverage"],
)


assert fused["evidence_count"] == 2
assert fused["coverage"]["coverage_ratio"] == 1.0
assert set(
    fused["coverage"]["covered_concepts"]
) == {
    "fever",
    "headache",
}


# =========================================================
# TEST 3 — DUPLICATE REMOVAL
# =========================================================

duplicate_results = [
    {
        "source": "World Health Organization",
        "title": "Malaria",
        "topic": "malaria",
        "evidence_type": "clinical_information",
        "evidence_context": "individual",
    },
    {
        "source": "World Health Organization",
        "title": "Malaria",
        "topic": "malaria",
        "evidence_type": "clinical_information",
        "evidence_context": "individual",
    },
]

fused = fuse_evidence(
    query="How can I prevent malaria?",
    concepts=[],
    results=duplicate_results,
    context={
        "context": "prevention",
        "confidence": 0.9,
    },
)

print("\nTEST 3 — DUPLICATE REMOVAL")

print(
    "Evidence count:",
    fused["evidence_count"],
)

assert fused["evidence_count"] == 1


# =========================================================
# TEST 4 — SOURCE AGREEMENT
# =========================================================

agreement_results = [
    {
        "source": "World Health Organization",
        "title": "Malaria",
        "topic": "malaria",
        "evidence_type": "clinical_information",
        "evidence_context": "individual",
    },
    {
        "source": (
            "National Library of Medicine / MedlinePlus"
        ),
        "title": "Fever",
        "topic": "fever",
        "evidence_type": "clinical_information",
        "evidence_context": "individual",
    },
]

fused = fuse_evidence(
    query="fever and malaria",
    concepts=[
        "fever",
        "malaria",
    ],
    results=agreement_results,
)

print("\nTEST 4 — SOURCE AGREEMENT")

print(
    "Source agreement:",
    fused["source_agreement"],
)

assert fused["source_agreement"]["source_count"] == 2


# =========================================================
# TEST 5 — POPULATION EVIDENCE
# =========================================================

population_results = [
    {
        "source": "World Health Organization",
        "title": (
            "Yellow fever - number of reported cases"
        ),
        "topic": "yellow fever",
        "evidence_type": (
            "public_health_statistic"
        ),
        "evidence_context": "population",
    }
]

fused = fuse_evidence(
    query=(
        "Number of reported yellow fever cases"
    ),
    concepts=[
        "yellow fever",
    ],
    results=population_results,
    context={
        "context": "population_health",
        "confidence": 0.95,
    },
)

print("\nTEST 5 — POPULATION EVIDENCE")

print(
    "Category distribution:",
    fused["category_distribution"],
)

print(
    "Coverage:",
    fused["coverage"],
)

assert fused["category_distribution"] == {
    "population": 1
}

assert fused["coverage"]["coverage_ratio"] == 1.0


# =========================================================
# TEST 6 — VACCINATION
# =========================================================

vaccination_results = [
    {
        "source": "World Health Organization",
        "title": (
            "Yellow fever vaccine (YFV) "
            "immunization coverage among 1-year olds (%)"
        ),
        "topic": "yellow fever",
        "evidence_type": (
            "vaccination_information"
        ),
        "evidence_context": "population",
    }
]

fused = fuse_evidence(
    query="Yellow fever vaccination coverage",
    concepts=[
        "yellow fever",
    ],
    results=vaccination_results,
    context={
        "context": "vaccination",
        "confidence": 1.0,
    },
)

print("\nTEST 6 — VACCINATION")

print(
    "Category distribution:",
    fused["category_distribution"],
)

assert fused["category_distribution"] == {
    "vaccination": 1
}


# =========================================================
# TEST 7 — EMPTY EVIDENCE
# =========================================================

fused = fuse_evidence(
    query="unknown health concern",
    concepts=[],
    results=[],
)

print("\nTEST 7 — EMPTY EVIDENCE")

print(
    "Status:",
    fused["status"],
)

assert fused["status"] == "no_evidence"
assert fused["evidence_count"] == 0


# =========================================================
# TEST 8 — V2.4 RESPONSE COMPATIBILITY
# =========================================================

retrieval_response = {
    "query": "I have a fever",
    "context": {
        "context": "individual_symptom",
        "confidence": 0.95,
    },
    "concepts": [
        "fever",
    ],
    "results": [
        {
            "source": (
                "National Library of Medicine / MedlinePlus"
            ),
            "title": "Fever",
            "topic": "fever",
            "evidence_type": "clinical_information",
            "evidence_context": "individual",
        }
    ],
}

fused = fuse_retrieval_response(
    retrieval_response
)

print("\nTEST 8 — V2.4 COMPATIBILITY")

print(
    "Status:",
    fused["status"],
)

assert fused["status"] == "evidence_fused"


print("\n" + "=" * 90)
print("ALL Q-CARE EVIDENCE FUSION V2.5 TESTS PASSED")
print("=" * 90)