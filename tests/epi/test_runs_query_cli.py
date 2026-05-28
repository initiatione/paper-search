import json
import sys

from epi.orchestrator import main
from epi.run_index import refresh_run_index


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_run(runs_root, run_id, *, workflow_type, state, status, paper_slug, next_actions=None, human_gate=None):
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        run_dir / "run-state.json",
        {
            "run_id": run_id,
            "workflow_type": workflow_type,
            "state": state,
            "status": status,
            "paper_slug": paper_slug,
            "started_at": f"{run_id}-start",
            "finished_at": f"{run_id}-finish",
        },
    )
    _write_json(
        run_dir / "report.json",
        {
            "next_actions": next_actions or [],
            "human_gate": human_gate,
        },
    )
    return run_dir


def _run_orchestrator_cli(monkeypatch, capsys, *args):
    monkeypatch.setattr(sys, "argv", ["epi.orchestrator", *args])
    exit_code = main()
    output = capsys.readouterr().out
    return exit_code, output


def test_runs_query_failed_filters_failed_runs_only(tmp_path, monkeypatch, capsys):
    vault = tmp_path / "vault"
    runs_root = vault / "_runs"
    _seed_run(
        runs_root,
        "20260528T100000Z-promote",
        workflow_type="promote-to-wiki",
        state="promoted",
        status="succeeded",
        paper_slug="paper-a",
    )
    _seed_run(
        runs_root,
        "20260528T101000Z-recritic",
        workflow_type="recritic",
        state="critic_failed",
        status="failed",
        paper_slug="paper-b",
    )
    refresh_run_index(vault)

    exit_code, output = _run_orchestrator_cli(monkeypatch, capsys, "runs-query", "--vault", str(vault), "--failed")

    assert exit_code == 0
    assert "20260528T101000Z-recritic" in output
    assert "20260528T100000Z-promote" not in output


def test_runs_query_human_gate_filters_pending_runs(tmp_path, monkeypatch, capsys):
    vault = tmp_path / "vault"
    runs_root = vault / "_runs"
    _seed_run(
        runs_root,
        "20260528T102000Z-ranked",
        workflow_type="advance-ranked",
        state="staging_ready",
        status="succeeded",
        paper_slug="paper-c",
        next_actions=["promote-after-approval"],
        human_gate={"status": "required"},
    )
    _seed_run(
        runs_root,
        "20260528T103000Z-repair",
        workflow_type="redo-read",
        state="reader_regenerated",
        status="succeeded",
        paper_slug="paper-d",
        next_actions=["recritic"],
    )
    refresh_run_index(vault)

    exit_code, output = _run_orchestrator_cli(monkeypatch, capsys, "runs-query", "--vault", str(vault), "--human-gate")

    assert exit_code == 0
    assert "20260528T102000Z-ranked" in output
    assert "20260528T103000Z-repair" not in output


def test_runs_query_latest_success_returns_only_latest_successful_workflow_run(tmp_path, monkeypatch, capsys):
    vault = tmp_path / "vault"
    runs_root = vault / "_runs"
    _seed_run(
        runs_root,
        "20260528T090000Z-promote-old",
        workflow_type="promote-to-wiki",
        state="promoted",
        status="succeeded",
        paper_slug="paper-old",
    )
    _seed_run(
        runs_root,
        "20260528T110000Z-promote-new",
        workflow_type="promote-to-wiki",
        state="promoted",
        status="succeeded",
        paper_slug="paper-new",
    )
    refresh_run_index(vault)

    exit_code, output = _run_orchestrator_cli(
        monkeypatch,
        capsys,
        "runs-query",
        "--vault",
        str(vault),
        "--latest-success",
        "promote-to-wiki",
    )

    assert exit_code == 0
    assert "20260528T110000Z-promote-new" in output
    assert "20260528T090000Z-promote-old" not in output


def test_runs_query_workflow_filters_recent_runs(tmp_path, monkeypatch, capsys):
    vault = tmp_path / "vault"
    runs_root = vault / "_runs"
    _seed_run(
        runs_root,
        "20260528T100000Z-ranked",
        workflow_type="advance-ranked",
        state="staging_ready",
        status="succeeded",
        paper_slug="paper-a",
    )
    _seed_run(
        runs_root,
        "20260528T101000Z-batch",
        workflow_type="advance-batch",
        state="critic_failed",
        status="failed",
        paper_slug="paper-b",
    )
    refresh_run_index(vault)

    exit_code, output = _run_orchestrator_cli(
        monkeypatch,
        capsys,
        "runs-query",
        "--vault",
        str(vault),
        "--workflow",
        "advance-ranked",
    )

    assert exit_code == 0
    assert "20260528T100000Z-ranked" in output
    assert "20260528T101000Z-batch" not in output
