from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


def test_skill_bundle_has_the_expected_entrypoints():
    expected = [
        "config-setup",
        "epi-paper-deposition",
        "mineru-paper-parser",
        "paper-discovery",
        "paper-ingest",
        "run-lifecycle",
        "skill-aware-evolve",
        "wiki-setup",
        "zotero-sync",
    ]

    for skill_name in expected:
        skill_path = SKILLS / skill_name / "SKILL.md"
        assert skill_path.exists(), skill_name


def test_paper_discovery_keeps_policy_in_skill_and_references():
    discovery = (SKILLS / "paper-discovery" / "SKILL.md").read_text(encoding="utf-8")

    assert "references/query-planner.md" in discovery
    assert "references/search-protocol.md" in discovery
    assert not (SKILLS / "paper-discovery" / "README.md").exists()


def test_epi_paper_deposition_documents_required_wiki_adapter_stack():
    deposition = (SKILLS / "epi-paper-deposition" / "SKILL.md").read_text(encoding="utf-8")

    assert "wiki_deposition_task.json" in deposition
    assert "epi-wiki-deposition" in deposition
    for skill in [
        "llm-wiki",
        "wiki-ingest",
        "wiki-context-pack",
        "wiki-lint",
        "wiki-stage-commit",
        "wiki-status",
        "wiki-query",
        "wiki-provenance",
        "tag-taxonomy",
    ]:
        assert skill in deposition
    for field in [
        "title",
        "category",
        "page_family",
        "sources",
        "summary",
        "provenance",
        "base_confidence",
        "lifecycle",
        "tier",
    ]:
        assert field in deposition
    assert "draft` or `review-needed`" in deposition
    assert "must not enter the formal graph" in deposition
