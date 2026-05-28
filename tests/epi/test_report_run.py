import json

from epi.report_run import write_report


def test_write_report_emits_required_sections_even_when_empty(tmp_path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True)

    write_report(
        run_dir,
        ranked=[
            {
                "title": "Embodied Navigation Control for Mobile Robots",
                "score": 0.91,
                "venue": "IROS",
                "year": 2024,
                "pdf_url": "https://example.org/nav.pdf",
            }
        ],
        errors=[],
        rejected=[],
        quarantined=[],
        critic_failures=[],
        budget_usage={"max_results": 5, "discovered_count": 1},
        wiki_pages_written=[],
        zotero_results={"status": "not_run", "records": []},
        next_actions=[],
    )

    report_json = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert report_json["accepted"][0]["title"] == "Embodied Navigation Control for Mobile Robots"
    assert report_json["rejected"] == []
    assert report_json["quarantined"] == []
    assert report_json["critic_failures"] == []
    assert report_json["budget_usage"] == {"max_results": 5, "discovered_count": 1}
    assert report_json["wiki_pages_written"] == []
    assert report_json["zotero_results"] == {"status": "not_run", "records": []}
    assert report_json["next_actions"] == []

    report_md = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "## Budget Usage" in report_md
    assert "## Next Actions" in report_md
