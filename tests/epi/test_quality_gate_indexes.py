import json

from epi.run_index import (
    refresh_run_index,
    query_by_benchmark_contract,
    query_by_quality_tier,
    query_runs,
)


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


def _make_ranked_paper(title, quality_tier, benchmark_signal=False):
    evidence = []
    cautions = []
    if benchmark_signal:
        evidence.append("benchmark_signal")
    else:
        cautions.append("weak_benchmark_signal")
    return {
        "title": title,
        "score": 0.85,
        "quality_tier": quality_tier,
        "quality_gate": {
            "schema_version": "epi-quality-gate-v1",
            "tier": quality_tier,
            "evidence": evidence,
            "cautions": cautions,
            "blocking_reasons": [],
        },
    }


def test_refresh_run_index_builds_quality_tier_index(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"

    _seed_run(
        runs_root,
        "run-tier-a",
        run_state={
            "run_id": "run-tier-a",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T01:00:00Z",
            "finished_at": "2026-06-01T01:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [
                _make_ranked_paper("Paper Alpha", "Tier A", benchmark_signal=True),
                _make_ranked_paper("Paper Beta", "Tier B", benchmark_signal=False),
            ],
        },
    )
    _seed_run(
        runs_root,
        "run-tier-b",
        run_state={
            "run_id": "run-tier-b",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T02:00:00Z",
            "finished_at": "2026-06-01T02:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [
                _make_ranked_paper("Paper Gamma", "Tier B", benchmark_signal=True),
                _make_ranked_paper("Paper Delta", "Tier C", benchmark_signal=False),
            ],
        },
    )

    index_payload = refresh_run_index(vault_path)

    assert "by_quality_tier" in index_payload
    tier_index = index_payload["by_quality_tier"]
    assert "Tier A" in tier_index
    assert "run-tier-a" in tier_index["Tier A"]
    assert "Tier B" in tier_index
    assert "run-tier-a" in tier_index["Tier B"]
    assert "run-tier-b" in tier_index["Tier B"]
    assert "Tier C" in tier_index
    assert "run-tier-b" in tier_index["Tier C"]


def test_refresh_run_index_builds_benchmark_contract_index(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"

    _seed_run(
        runs_root,
        "run-bench-valid",
        run_state={
            "run_id": "run-bench-valid",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T01:00:00Z",
            "finished_at": "2026-06-01T01:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [
                _make_ranked_paper("Paper Valid", "Tier A", benchmark_signal=True),
            ],
        },
    )
    _seed_run(
        runs_root,
        "run-bench-invalid",
        run_state={
            "run_id": "run-bench-invalid",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T02:00:00Z",
            "finished_at": "2026-06-01T02:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [
                _make_ranked_paper("Paper Invalid", "Tier C", benchmark_signal=False),
            ],
        },
    )

    index_payload = refresh_run_index(vault_path)

    assert "by_benchmark_contract" in index_payload
    bc_index = index_payload["by_benchmark_contract"]
    assert "run-bench-valid" in bc_index["valid_runs"]
    assert "run-bench-invalid" in bc_index["invalid_runs"]
    assert "run-bench-valid" not in bc_index["invalid_runs"]


def test_query_runs_filters_by_quality_tier(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"

    _seed_run(
        runs_root,
        "run-a",
        run_state={
            "run_id": "run-a",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T01:00:00Z",
            "finished_at": "2026-06-01T01:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [_make_ranked_paper("P1", "Tier A", benchmark_signal=True)],
        },
    )
    _seed_run(
        runs_root,
        "run-b",
        run_state={
            "run_id": "run-b",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T02:00:00Z",
            "finished_at": "2026-06-01T02:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [_make_ranked_paper("P2", "Tier C", benchmark_signal=False)],
        },
    )

    refresh_run_index(vault_path)

    result = query_runs(vault_path, quality_tier="Tier A")
    assert len(result["runs"]) == 1
    assert result["runs"][0]["run_id"] == "run-a"
    assert "quality_tier=Tier A" in result["title"]


def test_query_runs_filters_by_benchmark_valid(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"

    _seed_run(
        runs_root,
        "run-valid",
        run_state={
            "run_id": "run-valid",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T01:00:00Z",
            "finished_at": "2026-06-01T01:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [_make_ranked_paper("Bench Good", "Tier A", benchmark_signal=True)],
        },
    )
    _seed_run(
        runs_root,
        "run-invalid",
        run_state={
            "run_id": "run-invalid",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T02:00:00Z",
            "finished_at": "2026-06-01T02:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [_make_ranked_paper("Bench Bad", "Tier C", benchmark_signal=False)],
        },
    )

    refresh_run_index(vault_path)

    valid_result = query_runs(vault_path, benchmark_valid=True)
    assert len(valid_result["runs"]) == 1
    assert valid_result["runs"][0]["run_id"] == "run-valid"

    invalid_result = query_runs(vault_path, benchmark_valid=False)
    assert len(invalid_result["runs"]) == 1
    assert invalid_result["runs"][0]["run_id"] == "run-invalid"


def test_query_by_quality_tier_returns_tier_index(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"

    _seed_run(
        runs_root,
        "run-mixed",
        run_state={
            "run_id": "run-mixed",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T01:00:00Z",
            "finished_at": "2026-06-01T01:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [
                _make_ranked_paper("P1", "Tier A", benchmark_signal=True),
                _make_ranked_paper("P2", "Tier B", benchmark_signal=True),
            ],
        },
    )

    refresh_run_index(vault_path)

    result_all = query_by_quality_tier(vault_path)
    assert "tiers" in result_all
    assert "Tier A" in result_all["tiers"]
    assert "run-mixed" in result_all["tiers"]["Tier A"]

    result_a = query_by_quality_tier(vault_path, tier="Tier A")
    assert result_a["tier"] == "Tier A"
    assert len(result_a["runs"]) == 1
    assert result_a["runs"][0]["run_id"] == "run-mixed"


def test_query_by_benchmark_contract_returns_valid_and_invalid(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"

    _seed_run(
        runs_root,
        "run-bc",
        run_state={
            "run_id": "run-bc",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T01:00:00Z",
            "finished_at": "2026-06-01T01:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [
                _make_ranked_paper("Good Bench", "Tier A", benchmark_signal=True),
                _make_ranked_paper("Bad Bench", "Tier C", benchmark_signal=False),
            ],
        },
    )

    refresh_run_index(vault_path)

    valid_result = query_by_benchmark_contract(vault_path, valid=True)
    assert "run-bc" in valid_result["run_ids"]
    assert len(valid_result["runs"]) == 1

    invalid_result = query_by_benchmark_contract(vault_path, valid=False)
    assert "run-bc" in invalid_result["run_ids"]
    assert len(invalid_result["runs"]) == 1


def test_normalize_run_entry_extracts_quality_tier_summary(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"

    _seed_run(
        runs_root,
        "run-with-tiers",
        run_state={
            "run_id": "run-with-tiers",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T01:00:00Z",
            "finished_at": "2026-06-01T01:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [
                _make_ranked_paper("A1", "Tier A", benchmark_signal=True),
                _make_ranked_paper("A2", "Tier A", benchmark_signal=True),
                _make_ranked_paper("B1", "Tier B", benchmark_signal=False),
            ],
        },
    )

    index_payload = refresh_run_index(vault_path)

    entry = index_payload["runs"][0]
    assert entry["run_id"] == "run-with-tiers"
    assert entry["quality_tier_summary"] == {
        "tier_counts": {"Tier A": 2, "Tier B": 1},
        "total": 3,
    }


def test_normalize_run_entry_extracts_benchmark_contract_summary(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"

    _seed_run(
        runs_root,
        "run-bench-summary",
        run_state={
            "run_id": "run-bench-summary",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T01:00:00Z",
            "finished_at": "2026-06-01T01:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [
                _make_ranked_paper("Valid1", "Tier A", benchmark_signal=True),
                _make_ranked_paper("Invalid1", "Tier C", benchmark_signal=False),
                _make_ranked_paper("Invalid2", "Tier C", benchmark_signal=False),
            ],
        },
    )

    index_payload = refresh_run_index(vault_path)

    entry = index_payload["runs"][0]
    assert entry["run_id"] == "run-bench-summary"
    assert entry["benchmark_contract_summary"] == {"valid": 1, "invalid": 2}


def test_index_json_persists_quality_gate_indexes(tmp_path):
    vault_path = tmp_path / "vault"
    runs_root = vault_path / "_runs"

    _seed_run(
        runs_root,
        "run-persist",
        run_state={
            "run_id": "run-persist",
            "workflow_type": "paper-discovery-dry-run",
            "state": "completed",
            "status": "succeeded",
            "started_at": "2026-06-01T01:00:00Z",
            "finished_at": "2026-06-01T01:05:00Z",
        },
        report={
            "next_actions": [],
            "ranked": [
                _make_ranked_paper("P1", "Tier A", benchmark_signal=True),
            ],
        },
    )

    refresh_run_index(vault_path)

    index_path = runs_root / "index.json"
    assert index_path.exists()
    persisted = json.loads(index_path.read_text(encoding="utf-8"))
    assert "by_quality_tier" in persisted
    assert "by_benchmark_contract" in persisted
    assert "Tier A" in persisted["by_quality_tier"]
    assert "run-persist" in persisted["by_benchmark_contract"]["valid_runs"]
