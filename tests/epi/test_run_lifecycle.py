import json

from epi.run_index import prune_run_lifecycle


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed_run(vault, run_id, workflow="paper-discovery-dry-run", status="success"):
    run_dir = vault / "_runs" / run_id
    _write_json(
        run_dir / "run-state.json",
        {
            "run_id": run_id,
            "workflow_type": workflow,
            "status": status,
            "state": "done",
            "started_at": f"2026-05-29T00:00:0{run_id[-1]}+00:00",
            "finished_at": f"2026-05-29T00:00:1{run_id[-1]}+00:00",
        },
    )
    _write_json(run_dir / "report.json", {"next_actions": []})
    return run_dir


def test_run_lifecycle_dry_run_keeps_files_and_reports_candidates(tmp_path):
    vault = tmp_path / "vault"
    old_run = _seed_run(vault, "run-1")
    _seed_run(vault, "run-2")
    _seed_run(vault, "run-3")

    result = prune_run_lifecycle(vault, keep_latest=1, keep_per_workflow=0, apply=False)

    assert result["dry_run"] is True
    assert result["candidate_count"] == 2
    assert old_run.exists()
    assert (vault / "_meta" / "run-lifecycle").is_dir()


def test_run_lifecycle_apply_removes_only_terminal_candidates_and_refreshes_index(tmp_path):
    vault = tmp_path / "vault"
    removable = _seed_run(vault, "run-1")
    kept_recent = _seed_run(vault, "run-2")
    protected = _seed_run(vault, "run-3", status="running")

    result = prune_run_lifecycle(vault, keep_latest=1, keep_per_workflow=0, apply=True)

    assert result["dry_run"] is False
    assert result["deleted_count"] == 1
    assert not removable.exists()
    assert kept_recent.exists()
    assert protected.exists()
    index = json.loads((vault / "_runs" / "index.json").read_text(encoding="utf-8"))
    assert index["summary"]["total_runs"] == 2
