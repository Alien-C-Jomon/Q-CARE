from src.evidence_confidence import (
    calculate_confidence_profile,
)


print("\n" + "=" * 90)
print("Q-CARE EVIDENCE CONFIDENCE V2.6")
print("=" * 90)


# =========================================================
# TEST 1 — STRONG SINGLE SOURCE
# =========================================================

strong_single = {
    "evidence": [
        {
            "source": (
                "National Library of Medicine / MedlinePlus"
            ),
            "source_tier": 1,
            "category": "clinical",
        }
    ],
    "coverage": {
        "coverage_ratio": 1.0,
    },
    "source_agreement": {
        "source_count": 1,
    },
}

profile = calculate_confidence_profile(
    strong_single
)

print("\nTEST 1 — STRONG SINGLE SOURCE")
print(profile)

assert profile["source_quality"] == 1.0
assert profile["concept_coverage"] == 1.0
assert profile["overall_confidence"] > 0.70


# =========================================================
# TEST 2 — MULTIPLE TRUSTED SOURCES
# =========================================================

multiple_sources = {
    "evidence": [
        {
            "source": "World Health Organization",
            "source_tier": 1,
            "category": "clinical",
        },
        {
            "source": (
                "National Library of Medicine / MedlinePlus"
            ),
            "source_tier": 1,
            "category": "clinical",
        },
    ],
    "coverage": {
        "coverage_ratio": 1.0,
    },
    "source_agreement": {
        "source_count": 2,
    },
}

profile = calculate_confidence_profile(
    multiple_sources
)

print("\nTEST 2 — MULTIPLE TRUSTED SOURCES")
print(profile)

assert profile["source_quality"] == 1.0
assert profile["source_agreement"] == 0.85
assert profile["overall_confidence"] > 0.80


# =========================================================
# TEST 3 — PARTIAL COVERAGE
# =========================================================

partial = {
    "evidence": [
        {
            "source": "World Health Organization",
            "source_tier": 1,
            "category": "clinical",
        }
    ],
    "coverage": {
        "coverage_ratio": 0.5,
    },
    "source_agreement": {
        "source_count": 1,
    },
}

profile = calculate_confidence_profile(
    partial
)

print("\nTEST 3 — PARTIAL COVERAGE")
print(profile)

assert profile["concept_coverage"] == 0.5
assert profile["overall_confidence"] < 0.85


# =========================================================
# TEST 4 — LOW TRUST SOURCE
# =========================================================

low_trust = {
    "evidence": [
        {
            "source": "Unknown Website",
            "source_tier": 3,
            "category": "unknown",
        }
    ],
    "coverage": {
        "coverage_ratio": 1.0,
    },
    "source_agreement": {
        "source_count": 1,
    },
}

profile = calculate_confidence_profile(
    low_trust
)

print("\nTEST 4 — LOW TRUST SOURCE")
print(profile)

assert profile["source_quality"] == 0.60
assert profile["confidence_label"] in {
    "limited",
    "moderate",
}


# =========================================================
# TEST 5 — EMPTY EVIDENCE
# =========================================================

empty = {
    "evidence": [],
    "coverage": {
        "coverage_ratio": 0.0,
    },
    "source_agreement": {
        "source_count": 0,
    },
}

profile = calculate_confidence_profile(
    empty
)

print("\nTEST 5 — EMPTY EVIDENCE")
print(profile)

assert profile["overall_confidence"] == 0.0
assert profile["confidence_label"] == "insufficient"


# =========================================================
# TEST 6 — POPULATION EVIDENCE
# =========================================================

population = {
    "evidence": [
        {
            "source": "World Health Organization",
            "source_tier": 1,
            "category": "population",
        }
    ],
    "coverage": {
        "coverage_ratio": 1.0,
    },
    "source_agreement": {
        "source_count": 1,
    },
}

profile = calculate_confidence_profile(
    population
)

print("\nTEST 6 — POPULATION EVIDENCE")
print(profile)

assert profile["source_quality"] == 1.0
assert profile["evidence_strength"] == 0.85


# =========================================================
# TEST 7 — MULTI-SYMPTOM FULL COVERAGE
# =========================================================

multi_symptom = {
    "evidence": [
        {
            "source": (
                "National Library of Medicine / MedlinePlus"
            ),
            "source_tier": 1,
            "category": "clinical",
        },
        {
            "source": (
                "National Library of Medicine / MedlinePlus"
            ),
            "source_tier": 1,
            "category": "clinical",
        },
    ],
    "coverage": {
        "coverage_ratio": 1.0,
    },
    "source_agreement": {
        "source_count": 1,
    },
}

profile = calculate_confidence_profile(
    multi_symptom
)

print("\nTEST 7 — MULTI-SYMPTOM FULL COVERAGE")
print(profile)

assert profile["concept_coverage"] == 1.0
assert profile["evidence_strength"] == 1.0


# =========================================================
# TEST 8 — INTERPRETATION SAFETY
# =========================================================

assert (
    "not a diagnosis"
    in profile["interpretation"]
)

assert (
    "disease probability"
    in profile["interpretation"]
)


print("\n" + "=" * 90)
print("ALL Q-CARE EVIDENCE CONFIDENCE V2.6 TESTS PASSED")
print("=" * 90)