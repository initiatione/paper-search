import json

from epi.run_index import refresh_run_index


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_run(runs_root, run_id, run_state=None, report=None):
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    if run_state is not None:
        _write_json(run_dir / "run-state.json", run_state)
    if report is not None:
        _write_json(run_dir / "report.json", report)
    return run_dir


def test_refresh_run_index_writes_sorted_index_entries(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    _seed_run(
        runs_root,
        "20260528T090000Z-repair",
        run_state={
            "run_id": "20260528T090000Z-repair",
            "workflow_type": "redo-read",
            "state": "reader_regenerated",
            "status": "succeeded",
            "paper_slug": "paper-b",
            "started_at": "2026-05-28T09:00:00Z",
            "finished_at": "2026-05-28T09:05:00Z",
        },
        report={
            "next_actions": ["recritic"],
            "human_gate": None,
        },
    )
    _seed_run(
        runs_root,
        "20260528T100000Z-promote",
        run_state={
            "run_id": "20260528T100000Z-promote",
            "workflow_type": "promote-to-wiki",
            "state": "promoted",
            "status": "succeeded",
            "paper_slug": "paper-a",
            "started_at": "2026-05-28T10:00:00Z",
            "finished_at": "2026-05-28T10:15:00Z",
        },
        report={
            "next_actions": ["inspect-promoted-pages"],
            "human_gate": {"status": "approved", "approved_by": "codex-test"},
        },
    )
    _seed_run(
        runs_root,
        "20260528T093000Z-batch",
        run_state={
            "run_id": "20260528T093000Z-batch",
            "workflow_type": "advance-batch",
            "state": "critic_failed",
            "status": "failed",
            "paper_slug": None,
            "started_at": "2026-05-28T09:30:00Z",
            "finished_at": "2026-05-28T09:40:00Z",
        },
    )
    _seed_run(
        runs_root,
        "20260528T103000Z-ranked",
        run_state={
            "run_id": "20260528T103000Z-ranked",
            "workflow_type": "advance-ranked",
            "state": "staging_ready",
            "status": "succeeded",
            "paper_slug": "paper-c",
            "started_at": "2026-05-28T10:30:00Z",
            "finished_at": "2026-05-28T10:35:00Z",
        },
        report={
            "next_actions": ["await-human-approval"],
            "human_gate": {"status": "pending"},
        },
    )
    _seed_run(
        runs_root,
        "20260528T110000Z-report-only",
        report={
            "next_actions": ["should-not-crash"],
            "human_gate": None,
        },
    )

    refresh_run_index(vault_path)

    index_payload = json.loads((runs_root / "index.json").read_text(encoding="utf-8"))
    entries = index_payload["runs"]
    assert index_payload["summary"] == {
        "total_runs": 4,
        "workflow_counts": {
            "advance-batch": 1,
            "advance-ranked": 1,
            "promote-to-wiki": 1,
            "redo-read": 1,
        },
        "status_counts": {
            "failed": 1,
            "succeeded": 3,
        },
        "human_gate_pending_count": 1,
        "failed_run_count": 1,
    }
    assert [entry["run_id"] for entry in index_payload["latest_failures"]] == [
        "20260528T093000Z-batch",
    ]
    assert [entry["run_id"] for entry in index_payload["latest_human_gate_pending"]] == [
        "20260528T103000Z-ranked",
    ]
    assert index_payload["latest_success_by_workflow"] == {
        "advance-ranked": {
            "run_id": "20260528T103000Z-ranked",
            "workflow_type": "advance-ranked",
            "state": "staging_ready",
            "status": "succeeded",
            "paper_slug": "paper-c",
            "started_at": "2026-05-28T10:30:00Z",
            "finished_at": "2026-05-28T10:35:00Z",
            "next_actions": ["await-human-approval"],
            "human_gate": {"status": "pending"},
        },
        "promote-to-wiki": {
            "run_id": "20260528T100000Z-promote",
            "workflow_type": "promote-to-wiki",
            "state": "promoted",
            "status": "succeeded",
            "paper_slug": "paper-a",
            "started_at": "2026-05-28T10:00:00Z",
            "finished_at": "2026-05-28T10:15:00Z",
            "next_actions": ["inspect-promoted-pages"],
            "human_gate": {"status": "approved", "approved_by": "codex-test"},
        },
        "redo-read": {
            "run_id": "20260528T090000Z-repair",
            "workflow_type": "redo-read",
            "state": "reader_regenerated",
            "status": "succeeded",
            "paper_slug": "paper-b",
            "started_at": "2026-05-28T09:00:00Z",
            "finished_at": "2026-05-28T09:05:00Z",
            "next_actions": ["recritic"],
            "human_gate": None,
        },
    }
    assert [entry["run_id"] for entry in entries] == [
        "20260528T103000Z-ranked",
        "20260528T100000Z-promote",
        "20260528T093000Z-batch",
        "20260528T090000Z-repair",
    ]

    assert entries[1] == {
        "run_id": "20260528T100000Z-promote",
        "workflow_type": "promote-to-wiki",
        "state": "promoted",
        "status": "succeeded",
        "paper_slug": "paper-a",
        "started_at": "2026-05-28T10:00:00Z",
        "finished_at": "2026-05-28T10:15:00Z",
        "next_actions": ["inspect-promoted-pages"],
        "human_gate": {"status": "approved", "approved_by": "codex-test"},
    }
    assert entries[2]["next_actions"] == []
    assert entries[2]["human_gate"] is None


def test_refresh_run_index_writes_dashboard_and_skips_broken_runs(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    _seed_run(
        runs_root,
        "20260528T120000Z-ranked",
        run_state={
            "run_id": "20260528T120000Z-ranked",
            "workflow_type": "advance-ranked",
            "state": "staging_ready",
            "status": "succeeded",
            "paper_slug": "paper-c",
            "started_at": "2026-05-28T12:00:00Z",
            "finished_at": "2026-05-28T12:08:00Z",
        },
        report={
            "next_actions": ["promote-after-approval"],
            "human_gate": {"status": "required"},
        },
    )
    _seed_run(
        runs_root,
        "20260528T115000Z-recritic",
        run_state={
            "run_id": "20260528T115000Z-recritic",
            "workflow_type": "recritic",
            "state": "critic_failed",
            "status": "failed",
            "paper_slug": "paper-b",
            "started_at": "2026-05-28T11:50:00Z",
            "finished_at": "2026-05-28T11:55:00Z",
        },
        report={
            "next_actions": [],
            "human_gate": None,
        },
    )
    _seed_run(
        runs_root,
        "20260528T113000Z-promote",
        run_state={
            "run_id": "20260528T113000Z-promote",
            "workflow_type": "promote-to-wiki",
            "state": "promoted",
            "status": "succeeded",
            "paper_slug": "paper-a",
            "started_at": "2026-05-28T11:30:00Z",
            "finished_at": "2026-05-28T11:35:00Z",
        },
        report={
            "next_actions": ["inspect-promoted-pages"],
            "human_gate": None,
        },
    )
    broken_dir = runs_root / "broken-run"
    broken_dir.mkdir(parents=True, exist_ok=True)
    (broken_dir / "run-state.json").write_text("{not-json", encoding="utf-8")

    refresh_run_index(vault_path)

    dashboard_text = (runs_root / "dashboard.md").read_text(encoding="utf-8")
    failures_text = (runs_root / "dashboard-failures.md").read_text(encoding="utf-8")
    human_gate_text = (runs_root / "dashboard-human-gate.md").read_text(encoding="utf-8")
    success_text = (runs_root / "dashboard-recent-success.md").read_text(encoding="utf-8")
    assert dashboard_text.startswith("# EPI Run Dashboard")
    assert "## Summary" in dashboard_text
    assert "## Needs Attention" in dashboard_text
    assert "## Recent Failures" in dashboard_text
    assert "## Pending Human Gate" in dashboard_text
    assert "## Latest Success By Workflow" in dashboard_text
    assert "## Runs By Workflow" in dashboard_text
    assert "## Recent Runs" in dashboard_text
    assert "- total runs: 3" in dashboard_text
    assert "- advance-ranked: 1" in dashboard_text
    assert "- promote-to-wiki: 1" in dashboard_text
    assert "- recritic: 1" in dashboard_text

    needs_attention = dashboard_text.split("## Needs Attention", 1)[1].split("## Runs By Workflow", 1)[0]
    assert "20260528T120000Z-ranked" in needs_attention
    assert "20260528T115000Z-recritic" in needs_attention
    assert "20260528T113000Z-promote" in needs_attention

    recent_failures = dashboard_text.split("## Recent Failures", 1)[1].split("## Pending Human Gate", 1)[0]
    assert "20260528T115000Z-recritic" in recent_failures
    assert "20260528T120000Z-ranked" not in recent_failures

    pending_human_gate = dashboard_text.split("## Pending Human Gate", 1)[1].split("## Latest Success By Workflow", 1)[0]
    assert "20260528T120000Z-ranked" in pending_human_gate
    assert "20260528T115000Z-recritic" not in pending_human_gate

    latest_success_by_workflow = dashboard_text.split("## Latest Success By Workflow", 1)[1].split("## Runs By Workflow", 1)[0]
    assert "advance-ranked" in latest_success_by_workflow
    assert "promote-to-wiki" in latest_success_by_workflow
    assert latest_success_by_workflow.index("20260528T120000Z-ranked") < latest_success_by_workflow.index("20260528T113000Z-promote")

    recent_runs = dashboard_text.split("## Recent Runs", 1)[1]
    assert recent_runs.index("20260528T120000Z-ranked") < recent_runs.index("20260528T115000Z-recritic")
    assert recent_runs.index("20260528T115000Z-recritic") < recent_runs.index("20260528T113000Z-promote")
    assert "broken-run" not in dashboard_text

    assert failures_text.startswith("# EPI Failed Runs")
    assert "20260528T115000Z-recritic" in failures_text
    assert "20260528T120000Z-ranked" not in failures_text
    assert "20260528T113000Z-promote" not in failures_text

    assert human_gate_text.startswith("# EPI Human Gate Runs")
    assert "20260528T120000Z-ranked" in human_gate_text
    assert "20260528T115000Z-recritic" not in human_gate_text
    assert "20260528T113000Z-promote" not in human_gate_text

    assert success_text.startswith("# EPI Recent Successful Runs")
    assert success_text.index("20260528T120000Z-ranked") < success_text.index("20260528T113000Z-promote")
    assert "20260528T115000Z-recritic" not in success_text


def test_refresh_run_index_writes_empty_filtered_views_when_no_matches(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    _seed_run(
        runs_root,
        "20260528T130000Z-promote",
        run_state={
            "run_id": "20260528T130000Z-promote",
            "workflow_type": "promote-to-wiki",
            "state": "promoted",
            "status": "succeeded",
            "paper_slug": "paper-z",
            "started_at": "2026-05-28T13:00:00Z",
            "finished_at": "2026-05-28T13:05:00Z",
        },
        report={
            "next_actions": [],
            "human_gate": {"status": "approved", "approved_by": "codex-test"},
        },
    )

    refresh_run_index(vault_path)

    failures_text = (runs_root / "dashboard-failures.md").read_text(encoding="utf-8")
    human_gate_text = (runs_root / "dashboard-human-gate.md").read_text(encoding="utf-8")
    success_text = (runs_root / "dashboard-recent-success.md").read_text(encoding="utf-8")
    dashboard_text = (runs_root / "dashboard.md").read_text(encoding="utf-8")

    assert failures_text.startswith("# EPI Failed Runs")
    assert "No failed runs." in failures_text
    assert human_gate_text.startswith("# EPI Human Gate Runs")
    assert "No runs waiting on a human gate." in human_gate_text
    assert success_text.startswith("# EPI Recent Successful Runs")
    assert "20260528T130000Z-promote" in success_text
    assert "## Recent Failures" in dashboard_text
    assert "No failed runs." in dashboard_text
    assert "## Pending Human Gate" in dashboard_text
    assert "No runs waiting on a human gate." in dashboard_text
