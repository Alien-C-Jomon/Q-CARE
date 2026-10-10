
from src import evidence_engine


def test_evidence_query_normalization():
    assert evidence_engine.build_evidence_query("  high   fever  ") == "high fever"


def test_extract_fever_concept():
    assert "fever" in evidence_engine.extract_concepts("I have a high fever")


def test_empty_query_returns_invalid_input():
    result = evidence_engine.retrieve_evidence("")

    assert result["status"] == "invalid_input"
    assert result["results"] == []


def test_retrieve_evidence_without_live_network(monkeypatch):
    def fake_medlineplus(search_text, limit=10):
        return {
            "source": "National Library of Medicine / MedlinePlus",
            "status": "success",
            "results": [
                {
                    "title": f"Test information about {search_text}",
                    "topic": f"Test information about {search_text}",
                    "url": "https://medlineplus.gov/",
                    "summary": "Mock evidence for software testing.",
                    "evidence_type": "clinical_information",
                    "evidence_context": "individual",
                }
            ],
        }

    monkeypatch.setattr(
        evidence_engine,
        "query_medlineplus_content",
        fake_medlineplus,
    )

    result = evidence_engine.retrieve_evidence("I have a fever")

    assert result["status"] == "completed"
    assert "fever" in result["concepts"]
    assert len(result["results"]) >= 1
    assert (
        result["results"][0]["source"]
        == "National Library of Medicine / MedlinePlus"
    )
    assert result["results"][0]["tier"] == 1