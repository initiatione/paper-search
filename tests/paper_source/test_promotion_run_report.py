import json

from paper_source.report_run import write_report


def test_write_report_supports_promotion_routed_run_fields(tmp_path):
    run_dir = tmp_path / "promotion-run"
    run_dir.mkdir(parents=True)

    write_report(
        run_dir,
        ranked=[],
        errors=[],
        workflow_type="promote-to-wiki",
        run_id="promote-run-001",
        paper_states=[
            {
                "paper_slug": "fixture-paper",
                "state": "promoted",
                "next_action": "review-promoted-pages",
            }
        ],
        failed_papers=[],
        budget_usage={"paper_count": 1},
        wiki_pages_written=[
            "references/fixture-paper.md",
            "concepts/fixture-paper-concept.md",
            "synthesis/fixture-paper-synthesis.md",
        ],
        next_actions=["review-promoted-pages"],
        human_gate={"status": "approved", "approved_by": "codex-test"},
    )

    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report_json["workflow_type"] == "promote-to-wiki"
    assert report_json["paper_states"] == [
        {
            "paper_slug": "fixture-paper",
            "state": "promoted",
            "next_action": "review-promoted-pages",
        }
    ]
    assert report_json["wiki_pages_written"] == [
        "references/fixture-paper.md",
        "concepts/fixture-paper-concept.md",
        "synthesis/fixture-paper-synthesis.md",
    ]
    assert report_json["human_gate"] == {"status": "approved", "approved_by": "codex-test"}
    assert report_json["next_actions"] == ["review-promoted-pages"]

    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    assert report_md.startswith("# Paper Source Routed Run")
    assert "Workflow type: promote-to-wiki" in report_md
    assert "## Human Gate" in report_md
    assert "approved" in report_md
    assert "references/fixture-paper.md" in report_md


def test_write_report_supports_rollback_routed_run_fields(tmp_path):
    run_dir = tmp_path / "rollback-run"
    run_dir.mkdir(parents=True)

    write_report(
        run_dir,
        ranked=[],
        errors=[],
        workflow_type="rollback-promotion",
        run_id="rollback-run-001",
        paper_states=[
            {
                "paper_slug": "fixture-paper",
                "state": "rolled_back",
                "next_action": "inspect-rollback-log",
            }
        ],
        failed_papers=[],
        budget_usage={"paper_count": 1},
        wiki_pages_written=[],
        next_actions=["inspect-rollback-log"],
        restored_paths=["references/fixture-paper.md", "concepts/fixture-paper-concept.md"],
        removed_paths=["synthesis/fixture-paper-synthesis.md"],
    )

    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report_json["workflow_type"] == "rollback-promotion"
    assert report_json["wiki_pages_written"] == []
    assert report_json["restored_paths"] == [
        "references/fixture-paper.md",
        "concepts/fixture-paper-concept.md",
    ]
    assert report_json["removed_paths"] == ["synthesis/fixture-paper-synthesis.md"]
    assert report_json["next_actions"] == ["inspect-rollback-log"]

    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    assert report_md.startswith("# Paper Source Routed Run")
    assert "Workflow type: rollback-promotion" in report_md
    assert "## Restored Paths" in report_md
    assert "## Removed Paths" in report_md
    assert "synthesis/fixture-paper-synthesis.md" in report_md
