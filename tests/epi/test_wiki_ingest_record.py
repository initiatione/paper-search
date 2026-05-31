import json
import sys

import pytest

from epi.artifacts import file_sha256
from epi.orchestrator import main, record_wiki_ingest
from epi.paper_gate import build_paper_gate
from epi.wiki_ingest_record import create_wiki_ingest_record


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_agent_handoff(vault, slug="fixture-paper"):
    paper_root = vault / "_raw" / "papers" / slug
    staging_root = vault / "_staging" / "papers" / slug
    paper_root.mkdir(parents=True, exist_ok=True)
    staging_root.mkdir(parents=True, exist_ok=True)
    _write_json(
        paper_root / "metadata.json",
        {
            "slug": slug,
            "title": "Fixture Paper",
            "doi": "10.1000/fixture",
            "venue": "IROS",
        },
    )
    _write_json(
        paper_root / "critic" / "critic-report.json",
        {
            "outcome": "pass",
            "next_action": "stage",
            "hard_rule": "No critic pass, no compiled wiki write.",
            "reviewer_quorum_path": str(paper_root / "critic" / "critic-quorum.json"),
        },
    )
    _write_json(
        paper_root / "critic" / "critic-quorum.json",
        {
            "final_outcome": "pass",
            "reviewers": [{"name": "paper-quality-critic", "verdict": "pass"}],
        },
    )
    for relative in [
        "references/fixture-paper.md",
        "concepts/fixture-paper-concept.md",
        "synthesis/fixture-paper-synthesis.md",
        "reports/fixture-paper-reading-report.md",
    ]:
        path = staging_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n", encoding="utf-8")
    brief_path = staging_root / "wiki-ingest-brief.json"
    _write_json(
        brief_path,
        {
            "schema_version": "epi-wiki-ingest-brief-v1",
            "handoff_type": "agent-mediated-wiki-ingest",
            "paper_slug": slug,
            "title": "Fixture Paper",
            "wiki_framework_references": [
                {"name": "Ar9av/obsidian-wiki"},
                {"name": "kepano/obsidian-skills"},
                {"name": "initiatione/obsidian-wiki-dev"},
            ],
            "wiki_rule_source_model": {
                "resolution_order": [
                    {"source": "target vault AGENTS.md", "role": "owner contract"},
                    {"source": "_meta/schema.md", "role": "routing"},
                    {"source": "Ar9av/obsidian-wiki", "role": "framework"},
                    {"source": "kepano/obsidian-skills", "role": "format"},
                    {"source": "initiatione/obsidian-wiki-dev", "role": "personalized rules"},
                    {
                        "source": "local llm-wiki / wiki-ingest / obsidian-markdown skills",
                        "role": "execution adapters",
                    },
                ],
                "write_contract_requirements": [
                    "Keep Markdown vault files as the source of truth.",
                    "Search existing pages before creating duplicates.",
                    "Final wiki pages must be grounded in the source paper artifacts, not reader summaries alone.",
                ],
            },
            "ingest_policy": {
                "suggested_routes_only": True,
                "authority": "Resolve the target vault contract first.",
                "source_first_policy": "Read mineru/paper.md, mineru/paper.tex, mineru/images/*, and mineru/mineru-manifest.json before final wiki writing; reader outputs are navigation aids, not substitutes for the source paper.",
            },
            "source_bundle": {
                "raw_artifacts": [
                    "paper.pdf",
                    "metadata.json",
                    "mineru/paper.md",
                    "mineru/paper.tex",
                    "mineru/images/*",
                    "mineru/mineru-manifest.json",
                ],
                "formula_figure_review": {
                    "formulas": "Review formula notation and derivation cues before distilling claims.",
                    "figures_tables_images": "Interpret each figure, table, and image from mineru/images/*.",
                    "parse_uncertainty": "Inspect paper.pdf when parse limitations appear.",
                },
            },
        },
    )
    _write_json(
        staging_root / "promotion-plan.json",
        {
            "paper_slug": slug,
            "critic_outcome": "pass",
            "handoff_type": "agent-mediated-wiki-ingest",
            "wiki_write_model": "agent-mediated-vault-contract",
            "final_page_authority": "target-vault-contract-and-wiki-ingest-agent",
            "wiki_ingest_brief_path": str(brief_path),
            "agent_handoff_paths": [
                str(brief_path),
                str(staging_root / "reports" / "fixture-paper-reading-report.md"),
            ],
            "staged_reference": str(staging_root / "references" / "fixture-paper.md"),
            "staged_concepts": [str(staging_root / "concepts" / "fixture-paper-concept.md")],
            "staged_synthesis": [str(staging_root / "synthesis" / "fixture-paper-synthesis.md")],
            "staged_reports": [str(staging_root / "reports" / "fixture-paper-reading-report.md")],
        },
    )
    return slug


def _write_final_page(vault, relative, content):
    path = vault / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _enable_zotero(vault, *, collection="EPI Lab"):
    config = vault / "_meta" / "epi-config.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "\n".join(
            [
                "profile: general_academic_research",
                "zotero:",
                "  enabled: true",
                f"  collection: {json.dumps(collection)}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _run_orchestrator_cli(monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, "argv", ["epi.orchestrator", *args])
    exit_code = main()
    output = capsys.readouterr().out
    return exit_code, output


def test_record_wiki_ingest_records_agent_pages_without_modifying_them(tmp_path):
    vault = tmp_path / "vault"
    slug = _seed_agent_handoff(vault)
    reference = _write_final_page(vault, "papers/fixture-paper.md", "# Final Reference\n")
    concept = _write_final_page(vault, "concepts/fixture-concept.md", "# Final Concept\n")
    before_hashes = {path: file_sha256(path) for path in [reference, concept]}

    result = record_wiki_ingest(
        vault,
        slug,
        [str(reference), "concepts/fixture-concept.md"],
        approved_by="codex-test",
        notes="wiki agent applied target vault contract",
    )

    record = result["record"]
    assert record["status"] == "recorded"
    assert record["record_only"] is True
    assert record["compiled_wiki_write"] is False
    assert record["final_pages_modified_by_epi"] is False
    assert record["human_gate_decision"]["approved_by"] == "codex-test"
    assert record["source_first_confirmed"] is True
    assert record["relative_page_paths"] == [
        "papers/fixture-paper.md",
        "concepts/fixture-concept.md",
    ]
    assert [item["sha256"] for item in record["page_records"]] == [
        before_hashes[reference],
        before_hashes[concept],
    ]
    assert file_sha256(reference) == before_hashes[reference]
    assert file_sha256(concept) == before_hashes[concept]

    raw_record = json.loads((vault / "_raw" / "papers" / slug / "wiki-ingest-record.json").read_text(encoding="utf-8"))
    staging_record = json.loads(
        (vault / "_staging" / "papers" / slug / "wiki-ingest-record.json").read_text(encoding="utf-8")
    )
    assert raw_record["page_records"] == record["page_records"]
    assert staging_record["relative_page_paths"] == record["relative_page_paths"]

    gate = build_paper_gate(vault, slug)
    assert gate["status"] == "wiki_ingest_recorded"
    assert gate["next_action"] == "review-recorded-wiki-pages"
    checks = {run["name"]: run for run in gate["check_suite"]["check_runs"]}
    assert checks["human-approval"]["conclusion"] == "success"
    assert checks["human-approval"]["details"]["record_type"] == "wiki-ingest-record"

    run_dir = tmp_path / "vault" / "_runs" / result["run_id"]
    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    run_state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
    paper_state = json.loads((vault / "_raw" / "papers" / slug / "run-state.json").read_text(encoding="utf-8"))
    assert report_json["workflow_type"] == "record-wiki-ingest"
    assert report_json["wiki_pages_written"] == ["papers/fixture-paper.md", "concepts/fixture-concept.md"]
    assert report_json["human_gate"]["status"] == "approved"
    assert report_json["page_records"][0]["relative_path"] == "papers/fixture-paper.md"
    assert report_json["zotero_results"]["status"] == "skipped"
    assert report_json["zotero_results"]["reason"] == "zotero_not_configured"
    zotero_record = json.loads((vault / "_raw" / "papers" / slug / "zotero-record.json").read_text(encoding="utf-8"))
    assert zotero_record["wiki_ingest"]["final_wiki_pages"][0]["relative_path"] == "papers/fixture-paper.md"
    assert run_state["compiled_wiki_write"] is False
    assert run_state["record_only"] is True
    assert run_state["zotero_results"]["reason"] == "zotero_not_configured"
    assert paper_state["state"] == "wiki_ingest_recorded"
    assert paper_state["next_action"] == "review-recorded-wiki-pages"


def test_record_wiki_ingest_uses_enabled_zotero_config_in_report(tmp_path):
    vault = tmp_path / "vault"
    slug = _seed_agent_handoff(vault)
    _enable_zotero(vault, collection="Reading Lab")
    page = _write_final_page(vault, "papers/fixture-paper.md", "# Final Reference\n")

    result = record_wiki_ingest(vault, slug, [str(page)], approved_by="codex-test")

    raw_zotero = json.loads((vault / "_raw" / "papers" / slug / "zotero-record.json").read_text(encoding="utf-8"))
    assert raw_zotero["schema_version"] == "epi-zotero-record-v1"
    assert raw_zotero["status"] == "recorded"
    assert raw_zotero["record_only"] is True
    assert raw_zotero["collection"] == "Reading Lab"
    assert raw_zotero["paper_metadata"]["title"] == "Fixture Paper"
    assert raw_zotero["wiki_ingest"]["status"] == "recorded"
    assert raw_zotero["wiki_ingest"]["final_wiki_pages"][0]["relative_path"] == "papers/fixture-paper.md"

    run_dir = vault / "_runs" / result["run_id"]
    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    assert report_json["zotero_results"]["status"] == "recorded"
    assert report_json["zotero_results"]["collection"] == "Reading Lab"
    assert "## Zotero" in report_md
    assert "- status: recorded" in report_md
    assert "- final_wiki_pages: 1" in report_md


def test_create_wiki_ingest_record_rejects_missing_human_approval(tmp_path):
    vault = tmp_path / "vault"
    slug = _seed_agent_handoff(vault)
    page = _write_final_page(vault, "papers/fixture-paper.md", "# Final Reference\n")

    with pytest.raises(ValueError, match="human gate approval"):
        create_wiki_ingest_record(vault, slug, [str(page)], approved_by="")

    assert not (vault / "_raw" / "papers" / slug / "wiki-ingest-record.json").exists()


def test_create_wiki_ingest_record_rejects_pages_outside_vault(tmp_path):
    vault = tmp_path / "vault"
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")
    slug = _seed_agent_handoff(vault)

    with pytest.raises(ValueError, match="inside vault"):
        create_wiki_ingest_record(vault, slug, [str(outside)], approved_by="codex-test")


def test_create_wiki_ingest_record_rejects_internal_staging_page_as_final_page(tmp_path):
    vault = tmp_path / "vault"
    slug = _seed_agent_handoff(vault)
    staging_page = vault / "_staging" / "papers" / slug / "references" / "fixture-paper.md"

    with pytest.raises(ValueError, match="must not be under _staging"):
        create_wiki_ingest_record(vault, slug, [str(staging_page)], approved_by="codex-test")


def test_record_wiki_ingest_cli_outputs_json(tmp_path, monkeypatch, capsys):
    vault = tmp_path / "vault"
    slug = _seed_agent_handoff(vault)
    page = _write_final_page(vault, "papers/fixture-paper.md", "# Final Reference\n")

    exit_code, output = _run_orchestrator_cli(
        monkeypatch,
        capsys,
        "record-wiki-ingest",
        "--vault",
        str(vault),
        "--slug",
        slug,
        "--page",
        str(page),
        "--approved-by",
        "codex-test",
        "--json",
    )

    payload = json.loads(output)
    assert exit_code == 0
    assert payload["record"]["status"] == "recorded"
    assert payload["record"]["relative_page_paths"] == ["papers/fixture-paper.md"]
    assert payload["run_id"].startswith("record-wiki-ingest-")
    assert payload["zotero_results"]["status"] == "skipped"
    assert payload["zotero_record_path"].endswith("zotero-record.json")
