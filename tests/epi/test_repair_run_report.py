import json

from epi.report_run import write_report


def test_write_report_supports_redo_read_changed_artifacts(tmp_path):
    run_dir = tmp_path / "redo-read-run"
    run_dir.mkdir(parents=True)

    write_report(
        run_dir,
        ranked=[],
        errors=[],
        workflow_type="redo-read",
        run_id="redo-read-run-001",
        paper_states=[
            {
                "slug": "fixture-paper",
                "title": "Fixture Paper",
                "state": "reader_regenerated",
                "last_action": "redo-read",
                "next_action": "recritic",
                "human_gate_required": False,
            }
        ],
        failed_papers=[],
        budget_usage={"paper_count": 1},
        wiki_pages_written=[],
        next_actions=["recritic the regenerated reader outputs"],
        changed_artifacts=[
            "reader/reader.md",
            "reader/figures.md",
            "reader/reproducibility.md",
            "reader/implementation-ideas.md",
        ],
    )

    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report_json["workflow_type"] == "redo-read"
    assert report_json["changed_artifacts"] == [
        "reader/reader.md",
        "reader/figures.md",
        "reader/reproducibility.md",
        "reader/implementation-ideas.md",
    ]
    assert report_json["wiki_pages_written"] == []
    assert report_json["next_actions"] == ["recritic the regenerated reader outputs"]

    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    assert report_md.startswith("# EPI Routed Run")
    assert "Workflow type: redo-read" in report_md
    assert "## Changed Artifacts" in report_md
    assert "reader/implementation-ideas.md" in report_md


def test_write_report_supports_recritic_changed_artifacts(tmp_path):
    run_dir = tmp_path / "recritic-run"
    run_dir.mkdir(parents=True)

    write_report(
        run_dir,
        ranked=[],
        errors=[],
        workflow_type="recritic",
        run_id="recritic-run-001",
        paper_states=[
            {
                "slug": "fixture-paper",
                "title": "Fixture Paper",
                "state": "critic_passed",
                "last_action": "recritic",
                "next_action": "stage",
                "human_gate_required": False,
            }
        ],
        failed_papers=[],
        budget_usage={"paper_count": 1},
        wiki_pages_written=[],
        next_actions=["stage the paper for promotion review"],
        changed_artifacts=["critic/critic-report.json"],
    )

    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report_json["workflow_type"] == "recritic"
    assert report_json["changed_artifacts"] == ["critic/critic-report.json"]
    assert report_json["paper_states"] == [
        {
            "slug": "fixture-paper",
            "title": "Fixture Paper",
            "state": "critic_passed",
            "last_action": "recritic",
            "next_action": "stage",
            "human_gate_required": False,
        }
    ]

    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    assert report_md.startswith("# EPI Routed Run")
    assert "Workflow type: recritic" in report_md
    assert "## Changed Artifacts" in report_md
    assert "critic/critic-report.json" in report_md
