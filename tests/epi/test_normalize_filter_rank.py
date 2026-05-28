from epi.filter_candidates import filter_candidates
from epi.normalize_candidates import normalize_candidates
from epi.rank_papers import rank_candidates


def test_normalize_filter_rank_keeps_relevant_pdf_candidate():
    raw_records = [
        {
            "source": "semantic_scholar",
            "title": "Learning Agile Humanoid Motion Control",
            "authors": ["A. Researcher"],
            "year": 2025,
            "venue": "ICRA",
            "abstract": "Robot learning for humanoid motion control with reproducible experiments.",
            "doi": "10.1000/example",
            "pdf_url": "https://example.org/paper.pdf",
            "citation_count": 42,
            "code_url": "https://github.com/example/code",
        },
        {
            "source": "openalex",
            "title": "Learning Agile Humanoid Motion Control",
            "authors": ["A. Researcher"],
            "year": 2025,
            "venue": "ICRA",
            "abstract": "Robot learning for humanoid motion control with reproducible experiments.",
            "doi": "10.1000/example",
            "pdf_url": "https://example.org/paper.pdf",
            "citation_count": 40,
        },
    ]

    normalized = normalize_candidates(raw_records)
    filtered = filter_candidates(normalized, domains=["robotics", "control"], require_pdf=True)
    ranked = rank_candidates(filtered, positive_keywords=["humanoid", "control"], venue_tiers={"icra": 1.0})

    assert len(normalized) == 1
    assert filtered[0]["filter_status"] == "kept"
    assert ranked[0]["score"] > 0.75
    assert ranked[0]["sources"] == ["openalex", "semantic_scholar"]
