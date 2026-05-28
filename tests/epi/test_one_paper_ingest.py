import json

import pytest

from epi.orchestrator import run_one_paper_ingest
from epi.run_critic import run_critics
from epi.stage_wiki import stage_paper


def _write_phase2_fixture(tmp_path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\nfixture paper\n")
    mineru_md = tmp_path / "paper.md"
    mineru_md.write_text(
        "# Abstract\n\nThis paper presents embodied navigation control for mobile robots.\n\n"
        "# Method\n\nThe controller combines perception, planning, and feedback control.\n",
        encoding="utf-8",
    )
    mineru_tex = tmp_path / "paper.tex"
    mineru_tex.write_text("\\section{Abstract} Fixture paper.\n", encoding="utf-8")
    candidate = {
        "id": "doi:10.1000/nav",
        "slug": "embodied-navigation-control-for-mobile-robots",
        "title": "Embodied Navigation Control for Mobile Robots",
        "authors": ["B. Engineer"],
        "year": 2024,
        "venue": "IROS",
        "abstract": "Robotics navigation and control with code.",
        "doi": "10.1000/nav",
        "pdf_url": "file://fixture-paper.pdf",
        "citation_count": 9,
        "score": 0.82,
        "sources": ["fixture"],
    }
    return candidate, pdf, mineru_md, mineru_tex


def test_one_paper_ingest_preserves_raw_artifacts_and_stages_after_critic_pass(tmp_path):
    candidate, pdf, mineru_md, mineru_tex = _write_phase2_fixture(tmp_path)

    result = run_one_paper_ingest(
        vault_path=tmp_path / "vault",
        candidate=candidate,
        pdf_path=pdf,
        mineru_markdown_path=mineru_md,
        mineru_tex_path=mineru_tex,
    )

    paper_root = result["paper_root"]
    staging_root = result["staging_root"]
    slug = candidate["slug"]

    assert (paper_root / "paper.pdf").read_bytes() == pdf.read_bytes()
    assert (paper_root / "metadata.json").is_file()
    assert (paper_root / "acquire-record.json").is_file()
    assert (paper_root / "mineru" / "paper.md").is_file()
    assert (paper_root / "mineru" / "paper.tex").is_file()
    assert (paper_root / "reader" / "reader.md").read_text(encoding="utf-8").count("Evidence:") >= 2
    assert (paper_root / "critic" / "paper-quality-critic.md").is_file()
    assert (paper_root / "critic" / "parse-quality-critic.md").is_file()
    assert (paper_root / "critic" / "reader-quality-critic.md").is_file()
    assert (paper_root / "critic" / "critic-quorum.json").is_file()

    reader_record = result["run_manifest"]["reader_record"]
    parse_record = result["run_manifest"]["parse_record"]
    assert parse_record["started_at"]
    assert parse_record["finished_at"]
    assert parse_record["exit_status"] == 0
    assert parse_record["input_artifact_hashes"]["fixture_markdown"]
    assert parse_record["output_artifact_hashes"]["paper.md"]
    assert parse_record["output_artifact_hashes"]["paper.tex"]
    assert reader_record["started_at"]
    assert reader_record["finished_at"]
    assert reader_record["exit_status"] == 0
    assert reader_record["input_artifact_hashes"]["metadata.json"]
    assert reader_record["input_artifact_hashes"]["mineru/paper.md"]
    assert reader_record["output_artifact_hashes"]["reader.md"]
    assert reader_record["output_artifact_hashes"]["figures.md"]
    assert reader_record["output_artifact_hashes"]["reproducibility.md"]
    assert reader_record["output_artifact_hashes"]["implementation-ideas.md"]

    critic = json.loads((paper_root / "critic" / "critic-report.json").read_text(encoding="utf-8"))
    assert critic["outcome"] == "pass"
    assert critic["hard_rule"] == "No critic pass, no compiled wiki write."
    assert critic["reviewer_quorum_path"] == str(paper_root / "critic" / "critic-quorum.json")
    assert critic["reviewer_count"] == 3
    assert critic["disagreement"] is False

    quorum = json.loads((paper_root / "critic" / "critic-quorum.json").read_text(encoding="utf-8"))
    assert quorum["stage"] == "critic-quorum"
    assert quorum["final_outcome"] == "pass"
    assert quorum["disagreement"] is False
    assert [reviewer["name"] for reviewer in quorum["reviewers"]] == [
        "paper-quality-critic",
        "parse-quality-critic",
        "reader-quality-critic",
    ]
    for reviewer in quorum["reviewers"]:
        assert reviewer["mode"] == "local"
        assert reviewer["verdict"] == "pass"
        assert reviewer["scope"]
        assert reviewer["evidence"]

    assert (staging_root / "references" / f"{slug}.md").is_file()
    concept_path = staging_root / "concepts" / f"{slug}-concept.md"
    synthesis_path = staging_root / "synthesis" / f"{slug}-synthesis.md"
    assert concept_path.is_file()
    assert synthesis_path.is_file()
    assert f"reference_page: references/{slug}.md" in concept_path.read_text(encoding="utf-8")
    assert f"reference_page: references/{slug}.md" in synthesis_path.read_text(encoding="utf-8")
    promotion_plan = json.loads((staging_root / "promotion-plan.json").read_text(encoding="utf-8"))
    assert promotion_plan["critic_outcome"] == "pass"
    assert promotion_plan["staged_reference"] == str(staging_root / "references" / f"{slug}.md")
    assert promotion_plan["staged_concepts"] == [str(concept_path)]
    assert promotion_plan["staged_synthesis"] == [str(synthesis_path)]
    assert promotion_plan["compiled_targets"] == [
        f"references/{slug}.md",
        f"concepts/{slug}-concept.md",
        f"synthesis/{slug}-synthesis.md",
    ]
    assert not (tmp_path / "vault" / "references" / f"{slug}.md").exists()


def test_stage_paper_rejects_nonpassing_critic(tmp_path):
    paper_root = tmp_path / "_raw" / "papers" / "paper"
    critic_dir = paper_root / "critic"
    reader_dir = paper_root / "reader"
    critic_dir.mkdir(parents=True)
    reader_dir.mkdir(parents=True)
    (reader_dir / "reader.md").write_text("# Reader\n", encoding="utf-8")
    (critic_dir / "critic-report.json").write_text(
        json.dumps({"outcome": "revise-reader", "hard_rule": "No critic pass, no compiled wiki write."}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="critic outcome"):
        stage_paper(tmp_path, "paper", paper_root)

    assert not (tmp_path / "_staging" / "papers" / "paper").exists()


def test_critic_quorum_records_reviewer_failure_without_staging(tmp_path):
    vault = tmp_path / "vault"
    slug = "paper"
    paper_root = vault / "_raw" / "papers" / slug
    (paper_root / "mineru").mkdir(parents=True)
    (paper_root / "reader").mkdir(parents=True)
    (paper_root / "paper.pdf").write_bytes(b"%PDF-1.4\n")
    (paper_root / "metadata.json").write_text(json.dumps({"slug": slug}), encoding="utf-8")
    (paper_root / "mineru" / "paper.md").write_text("# Paper\n\nParsed content.\n", encoding="utf-8")
    (paper_root / "reader" / "reader.md").write_text("# Reader\n\nUnsupported claim.\n", encoding="utf-8")

    critic = run_critics(paper_root)

    assert critic["outcome"] == "revise-reader"
    assert critic["next_action"] == "revise-reader"
    assert critic["reviewer_count"] == 3
    assert critic["disagreement"] is True
    quorum = json.loads((paper_root / "critic" / "critic-quorum.json").read_text(encoding="utf-8"))
    assert quorum["final_outcome"] == "revise-reader"
    assert quorum["disagreement"] is True
    assert [reviewer["verdict"] for reviewer in quorum["reviewers"]] == ["pass", "pass", "fail"]

    with pytest.raises(ValueError, match="critic outcome"):
        stage_paper(vault, slug, paper_root)

    assert not (vault / "_staging" / "papers" / slug).exists()


def test_critic_quorum_records_missing_reader_as_reviewer_failure(tmp_path):
    slug = "paper"
    paper_root = tmp_path / "_raw" / "papers" / slug
    (paper_root / "mineru").mkdir(parents=True)
    (paper_root / "paper.pdf").write_bytes(b"%PDF-1.4\n")
    (paper_root / "metadata.json").write_text(json.dumps({"slug": slug}), encoding="utf-8")
    (paper_root / "mineru" / "paper.md").write_text("# Paper\n\nParsed content.\n", encoding="utf-8")

    critic = run_critics(paper_root)

    assert critic["outcome"] == "revise-reader"
    assert critic["disagreement"] is True
    quorum = json.loads((paper_root / "critic" / "critic-quorum.json").read_text(encoding="utf-8"))
    reader_reviewer = quorum["reviewers"][2]
    assert reader_reviewer["name"] == "reader-quality-critic"
    assert reader_reviewer["verdict"] == "fail"
    assert "reader/reader.md missing" in reader_reviewer["evidence"]
