import json
import sys

import pytest

from epi.orchestrator import main
from epi.promote_to_wiki import promote_paper, rollback_promotion


def _compiled_page_set(vault, slug):
    return {
        "reference": vault / "references" / f"{slug}.md",
        "concept": vault / "concepts" / f"{slug}-concept.md",
        "synthesis": vault / "synthesis" / f"{slug}-synthesis.md",
    }


def _run_orchestrator_cli(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["epi.orchestrator", *args])
    return main()


def _run_dirs(vault):
    return [path for path in (vault / "_runs").iterdir() if path.is_dir()]


def _seed_staged_paper(vault, slug, *, outcome="pass", existing_compiled=None, existing_compiled_pages=None):
    paper_root = vault / "_raw" / "papers" / slug
    staging_root = vault / "_staging" / "papers" / slug
    (paper_root / "critic").mkdir(parents=True)
    (staging_root / "references").mkdir(parents=True)
    (staging_root / "concepts").mkdir(parents=True)
    (staging_root / "synthesis").mkdir(parents=True)
    (paper_root / "metadata.json").write_text(
        json.dumps({"slug": slug, "title": "Fixture Paper", "doi": "10.1000/fixture"}),
        encoding="utf-8",
    )
    (paper_root / "critic" / "critic-report.json").write_text(
        json.dumps({"outcome": outcome, "hard_rule": "No critic pass, no compiled wiki write."}),
        encoding="utf-8",
    )
    (staging_root / "references" / f"{slug}.md").write_text(
        "---\nstage: staging\n---\n\n# Fixture Paper\n",
        encoding="utf-8",
    )
    (staging_root / "concepts" / f"{slug}-concept.md").write_text(
        "---\nstage: staging\npage_type: concept\n---\n\n# Fixture Paper Concept\n",
        encoding="utf-8",
    )
    (staging_root / "synthesis" / f"{slug}-synthesis.md").write_text(
        "---\nstage: staging\npage_type: synthesis\n---\n\n# Fixture Paper Synthesis\n",
        encoding="utf-8",
    )
    (staging_root / "promotion-plan.json").write_text(
        json.dumps(
            {
                "paper_slug": slug,
                "critic_outcome": outcome,
                "staged_reference": str(staging_root / "references" / f"{slug}.md"),
                "staged_concepts": [str(staging_root / "concepts" / f"{slug}-concept.md")],
                "staged_synthesis": [str(staging_root / "synthesis" / f"{slug}-synthesis.md")],
                "compiled_targets": [
                    f"references/{slug}.md",
                    f"concepts/{slug}-concept.md",
                    f"synthesis/{slug}-synthesis.md",
                ],
            }
        ),
        encoding="utf-8",
    )
    (vault / ".manifest.json").write_text(
        json.dumps({"vault_type": "engineering-paper-research", "papers": []}),
        encoding="utf-8",
    )
    (vault / "log.md").write_text("# Log\n", encoding="utf-8")
    (vault / "index.md").write_text("# Paper Research Wiki\n\nOriginal index intro.\n", encoding="utf-8")
    (vault / "hot.md").write_text("# Hot\n\nOriginal hot intro.\n", encoding="utf-8")
    compiled_pages = _compiled_page_set(vault, slug)
    if existing_compiled is not None:
        compiled_pages["reference"].parent.mkdir(parents=True, exist_ok=True)
        compiled_pages["reference"].write_text(existing_compiled, encoding="utf-8")
    for page_type, content in (existing_compiled_pages or {}).items():
        compiled_pages[page_type].parent.mkdir(parents=True, exist_ok=True)
        compiled_pages[page_type].write_text(content, encoding="utf-8")
    return paper_root, staging_root


def test_promote_paper_writes_compiled_reference_and_records_backup(tmp_path):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    paper_root, _ = _seed_staged_paper(vault, slug, existing_compiled="# Old Page\n")

    record = promote_paper(vault, slug, approved_by="codex-test")

    compiled = vault / "references" / f"{slug}.md"
    assert compiled.read_text(encoding="utf-8").startswith("---\nstage: staging")
    promotion_record = json.loads((paper_root / "promotion-record.json").read_text(encoding="utf-8"))
    assert promotion_record["status"] == "promoted"
    assert promotion_record["critic_outcome"] == "pass"
    assert promotion_record["promoted_page_paths"][0] == str(compiled)
    assert str(vault / "concepts" / f"{slug}-concept.md") in promotion_record["promoted_page_paths"]
    assert str(vault / "synthesis" / f"{slug}-synthesis.md") in promotion_record["promoted_page_paths"]
    assert promotion_record["previous_page_snapshot_paths"]
    assert promotion_record["human_gate_decision"]["status"] == "approved"
    assert promotion_record["human_gate_decision"]["approved_by"] == "codex-test"
    assert record["backup_paths"] == promotion_record["previous_page_snapshot_paths"]

    manifest = json.loads((vault / ".manifest.json").read_text(encoding="utf-8"))
    assert manifest["papers"][0]["slug"] == slug
    assert manifest["papers"][0]["promotion_status"] == "promoted"
    assert "Promoted fixture-paper" in (vault / "log.md").read_text(encoding="utf-8")


def test_promote_paper_rejects_nonpassing_critic(tmp_path):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    _seed_staged_paper(vault, slug, outcome="human-review")

    with pytest.raises(ValueError, match="critic outcome"):
        promote_paper(vault, slug)

    assert not (vault / "references" / f"{slug}.md").exists()


def test_promote_paper_rejects_missing_human_gate_approval(tmp_path):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    _seed_staged_paper(vault, slug)

    with pytest.raises(ValueError, match="human gate approval"):
        promote_paper(vault, slug)

    assert not (vault / "references" / f"{slug}.md").exists()
    assert not (vault / "_raw" / "papers" / slug / "promotion-record.json").exists()


def test_promote_paper_writes_compiled_concept_and_synthesis_pages(tmp_path):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    paper_root, staging_root = _seed_staged_paper(
        vault,
        slug,
        existing_compiled="# Old Reference\n",
        existing_compiled_pages={"concept": "# Old Concept\n"},
    )

    promote_paper(vault, slug, approved_by="codex-test")

    compiled_pages = _compiled_page_set(vault, slug)
    assert compiled_pages["reference"].read_text(encoding="utf-8").startswith("---\nstage: staging")
    assert compiled_pages["concept"].read_text(encoding="utf-8").startswith("---\nstage: staging")
    assert compiled_pages["synthesis"].read_text(encoding="utf-8").startswith("---\nstage: staging")

    promotion_record = json.loads((paper_root / "promotion-record.json").read_text(encoding="utf-8"))
    assert promotion_record["staged_draft_paths"] == [
        str(staging_root / "references" / f"{slug}.md"),
        str(staging_root / "concepts" / f"{slug}-concept.md"),
        str(staging_root / "synthesis" / f"{slug}-synthesis.md"),
    ]
    assert promotion_record["promoted_page_paths"] == [
        str(compiled_pages["reference"]),
        str(compiled_pages["concept"]),
        str(compiled_pages["synthesis"]),
    ]
    page_records = {entry["compiled_path"]: entry for entry in promotion_record["page_transactions"]}
    assert page_records[str(compiled_pages["reference"])]["previous_snapshot_path"]
    assert page_records[str(compiled_pages["concept"])]["previous_snapshot_path"]
    assert page_records[str(compiled_pages["synthesis"])]["previous_snapshot_path"] is None


def test_rollback_promotion_restores_previous_page(tmp_path):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    _seed_staged_paper(vault, slug, existing_compiled="# Old Page\n")
    promote_paper(vault, slug, approved_by="codex-test")

    rollback = rollback_promotion(vault, slug)

    assert rollback["status"] == "rolled_back"
    assert (vault / "references" / f"{slug}.md").read_text(encoding="utf-8") == "# Old Page\n"
    manifest = json.loads((vault / ".manifest.json").read_text(encoding="utf-8"))
    assert manifest["papers"] == []
    assert "Rolled back fixture-paper" in (vault / "log.md").read_text(encoding="utf-8")
    assert rollback["restored_state_paths"]["manifest"] == str(vault / ".manifest.json")


def test_rollback_promotion_restores_or_removes_concept_and_synthesis_pages(tmp_path):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    _seed_staged_paper(
        vault,
        slug,
        existing_compiled="# Old Reference\n",
        existing_compiled_pages={"concept": "# Old Concept\n"},
    )
    promote_paper(vault, slug, approved_by="codex-test")

    rollback = rollback_promotion(vault, slug)

    compiled_pages = _compiled_page_set(vault, slug)
    assert compiled_pages["reference"].read_text(encoding="utf-8") == "# Old Reference\n"
    assert compiled_pages["concept"].read_text(encoding="utf-8") == "# Old Concept\n"
    assert not compiled_pages["synthesis"].exists()
    assert sorted(rollback["restored_paths"]) == sorted(
        [str(compiled_pages["reference"]), str(compiled_pages["concept"])]
    )
    assert rollback["removed_paths"] == [str(compiled_pages["synthesis"])]


def test_promotion_snapshots_manifest_and_log_for_rollback(tmp_path):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    paper_root, _ = _seed_staged_paper(vault, slug)
    original_manifest = {
        "vault_type": "engineering-paper-research",
        "papers": [{"slug": "old-paper", "promotion_status": "promoted"}],
    }
    original_log = "# Log\n- Existing entry.\n"
    (vault / ".manifest.json").write_text(json.dumps(original_manifest), encoding="utf-8")
    (vault / "log.md").write_text(original_log, encoding="utf-8")

    promote_paper(vault, slug, approved_by="codex-test")
    promotion_record = json.loads((paper_root / "promotion-record.json").read_text(encoding="utf-8"))

    snapshot_paths = promotion_record["previous_state_snapshot_paths"]
    assert set(snapshot_paths) == {"manifest", "log", "index", "hot"}
    assert json.loads((paper_root / snapshot_paths["manifest"]).read_text(encoding="utf-8")) == original_manifest
    assert (paper_root / snapshot_paths["log"]).read_text(encoding="utf-8") == original_log
    assert promotion_record["manifest_update_summary"]["paper_slug"] == slug
    assert "Promoted fixture-paper" in (vault / "log.md").read_text(encoding="utf-8")

    rollback = rollback_promotion(vault, slug)

    assert rollback["status"] == "rolled_back"
    assert json.loads((vault / ".manifest.json").read_text(encoding="utf-8")) == original_manifest
    restored_log = (vault / "log.md").read_text(encoding="utf-8")
    assert restored_log.startswith(original_log)
    assert "Promoted fixture-paper" not in restored_log
    assert "Rolled back fixture-paper" in restored_log
    assert rollback["restored_state_paths"] == {
        "manifest": str(vault / ".manifest.json"),
        "log": str(vault / "log.md"),
        "index": str(vault / "index.md"),
        "hot": str(vault / "hot.md"),
    }


def test_promotion_refreshes_index_and_hot_and_rolls_them_back(tmp_path):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    paper_root, _ = _seed_staged_paper(vault, slug)
    original_index = "# Paper Research Wiki\n\nOriginal index intro.\n"
    original_hot = "# Hot\n\nOriginal hot intro.\n"
    (vault / "index.md").write_text(original_index, encoding="utf-8")
    (vault / "hot.md").write_text(original_hot, encoding="utf-8")

    promote_paper(vault, slug, approved_by="codex-test")

    promotion_record = json.loads((paper_root / "promotion-record.json").read_text(encoding="utf-8"))
    snapshot_paths = promotion_record["previous_state_snapshot_paths"]
    assert (paper_root / snapshot_paths["index"]).read_text(encoding="utf-8") == original_index
    assert (paper_root / snapshot_paths["hot"]).read_text(encoding="utf-8") == original_hot
    index_text = (vault / "index.md").read_text(encoding="utf-8")
    hot_text = (vault / "hot.md").read_text(encoding="utf-8")
    assert "Original index intro." in index_text
    assert "Original hot intro." in hot_text
    assert "<!-- EPI:PROMOTED-PAPERS:START -->" in index_text
    assert "<!-- EPI:HOT-PAPERS:START -->" in hot_text
    assert "[[references/fixture-paper|Fixture Paper]]" in index_text
    assert "[[references/fixture-paper|Fixture Paper]]" in hot_text
    assert "10.1000/fixture" in index_text

    rollback = rollback_promotion(vault, slug)

    assert rollback["restored_state_paths"]["index"] == str(vault / "index.md")
    assert rollback["restored_state_paths"]["hot"] == str(vault / "hot.md")
    assert (vault / "index.md").read_text(encoding="utf-8") == original_index
    assert (vault / "hot.md").read_text(encoding="utf-8") == original_hot


def test_promote_to_wiki_cli_writes_routed_report_with_human_gate_and_all_pages(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    _seed_staged_paper(vault, slug)

    exit_code = _run_orchestrator_cli(
        monkeypatch,
        "promote-to-wiki",
        "--vault",
        str(vault),
        "--slug",
        slug,
        "--approved-by",
        "codex-test",
    )

    assert exit_code == 0
    run_dirs = _run_dirs(vault)
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    index_payload = json.loads((vault / "_runs" / "index.json").read_text(encoding="utf-8"))
    dashboard_text = (vault / "_runs" / "dashboard.md").read_text(encoding="utf-8")
    compiled_pages = _compiled_page_set(vault, slug)
    expected_written = [
        str(compiled_pages["reference"]),
        str(compiled_pages["concept"]),
        str(compiled_pages["synthesis"]),
    ]

    assert report_json["workflow_type"] == "promote-to-wiki"
    assert report_json["paper_states"] == [
        {"paper_slug": slug, "state": "promoted", "next_action": "review-promoted-pages"}
    ]
    assert report_json["failed_papers"] == []
    assert sorted(report_json["wiki_pages_written"]) == sorted(expected_written)
    assert report_json["human_gate"]["status"] == "approved"
    assert report_json["human_gate"]["approved_by"] == "codex-test"
    assert report_json["next_actions"] == ["review-promoted-pages"]
    assert "approved" in report_md
    for path in expected_written:
        assert path in report_md
    assert index_payload["runs"][0]["run_id"] == run_dir.name
    assert index_payload["runs"][0]["workflow_type"] == "promote-to-wiki"
    assert run_dir.name in dashboard_text


def test_rollback_promotion_cli_writes_routed_report_with_restored_and_removed_paths(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    _seed_staged_paper(
        vault,
        slug,
        existing_compiled="# Old Reference\n",
        existing_compiled_pages={"concept": "# Old Concept\n"},
    )
    promote_paper(vault, slug, approved_by="codex-test")

    exit_code = _run_orchestrator_cli(
        monkeypatch,
        "rollback-promotion",
        "--vault",
        str(vault),
        "--slug",
        slug,
    )

    assert exit_code == 0
    run_dirs = _run_dirs(vault)
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    compiled_pages = _compiled_page_set(vault, slug)
    expected_restored = [str(compiled_pages["reference"]), str(compiled_pages["concept"])]
    expected_removed = [str(compiled_pages["synthesis"])]

    assert report_json["workflow_type"] == "rollback-promotion"
    assert report_json["paper_states"] == [
        {"paper_slug": slug, "state": "rolled_back", "next_action": "re-review-before-repromote"}
    ]
    assert report_json["failed_papers"] == []
    assert report_json["wiki_pages_written"] == []
    assert sorted(report_json["restored_paths"]) == sorted(expected_restored)
    assert report_json["removed_paths"] == expected_removed
    assert report_json["next_actions"] == ["re-review-before-repromote"]
    for path in expected_restored + expected_removed:
        assert path in report_md
