import json
from pathlib import Path

import pytest

from epi.feedback import record_feedback
from epi.skill_aware_evolve import activate_evolution, propose_evolution
from epi.zotero_sync import sync_zotero_record


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_templates(vault_path: Path) -> None:
    _write_text(
        vault_path / "templates" / "ranking.example.yaml",
        "\n".join(
            [
                "weights:",
                "  topic_relevance: 0.35",
                "  reproducibility_signal: 0.06",
                "",
            ]
        ),
    )
    _write_text(
        vault_path / "templates" / "critic-checklist.example.yaml",
        "\n".join(
            [
                "paper_quality_critic:",
                "  enabled_from_phase: 2",
                "",
            ]
        ),
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_zotero_sync_disabled_writes_skip_record(tmp_path):
    paper_root = tmp_path / "_raw" / "papers" / "paper"
    paper_root.mkdir(parents=True)

    record = sync_zotero_record(paper_root, enabled=False, collection="EPI")

    assert record["status"] == "skipped"
    assert record["reason"] == "zotero_disabled"
    written = json.loads((paper_root / "zotero-record.json").read_text(encoding="utf-8"))
    assert written["collection"] == "EPI"


def test_record_feedback_appends_jsonl(tmp_path):
    first = record_feedback(
        tmp_path,
        feedback_type="reader-correction",
        target="paper/reader.md",
        message="Claim needs stronger evidence.",
        source="human",
    )
    second = record_feedback(
        tmp_path,
        feedback_type="plugin-eval",
        target="plugins/epi",
        message="Token budget warning reviewed.",
        source="plugin-eval",
    )

    feedback_log = tmp_path / "_runs" / "feedback.jsonl"
    rows = [json.loads(line) for line in feedback_log.read_text(encoding="utf-8").splitlines()]
    assert [row["id"] for row in rows] == [first["id"], second["id"]]
    assert rows[0]["type"] == "reader-correction"
    assert rows[1]["source"] == "plugin-eval"


def test_record_feedback_updates_run_local_summary_when_run_id_is_provided(tmp_path):
    first = record_feedback(
        tmp_path,
        feedback_type="reader-correction",
        target="paper/reader.md",
        message="Need better traceability for claim 2.",
        source="human",
        run_id="run-123",
    )
    second = record_feedback(
        tmp_path,
        feedback_type="plugin-eval",
        target="plugins/epi",
        message="Whitelist policy confirmed.",
        source="plugin-eval",
        run_id="run-123",
    )

    feedback_log = tmp_path / "_runs" / "feedback.jsonl"
    rows = [json.loads(line) for line in feedback_log.read_text(encoding="utf-8").splitlines()]
    assert [row["run_id"] for row in rows] == ["run-123", "run-123"]

    summary = _read_json(tmp_path / "_runs" / "run-123" / "feedback-summary.json")
    assert summary["run_id"] == "run-123"
    assert summary["feedback_count"] == 2
    assert summary["feedback_ids"] == [first["id"], second["id"]]
    assert summary["last_feedback_id"] == second["id"]


def test_evolution_proposal_requires_approval_before_activation_and_applies_whitelisted_asset(tmp_path):
    _seed_templates(tmp_path)
    proposal = propose_evolution(
        tmp_path,
        reflection_type="OPTIMIZATION",
        target_asset="templates/ranking.example.yaml",
        rationale="Boost reproducibility signal after repeated user feedback.",
        proposed_change={"weights": {"reproducibility_signal": 0.12}},
        evidence=["_runs/feedback.jsonl#1"],
    )

    proposal_path = tmp_path / "_evolution" / "proposals" / f"{proposal['id']}.json"
    assert proposal_path.is_file()

    with pytest.raises(PermissionError, match="approval"):
        activate_evolution(tmp_path, proposal["id"], approved=False)

    activated = activate_evolution(tmp_path, proposal["id"], approved=True)

    assert activated["status"] == "active"
    assert activated["code_modified"] is False
    assert activated["asset_application"]["status"] == "applied"
    assert (tmp_path / "_evolution" / "active" / f"{proposal['id']}.json").is_file()
    assert "reproducibility_signal: 0.12" in (
        tmp_path / "templates" / "ranking.example.yaml"
    ).read_text(encoding="utf-8")


def test_activate_evolution_keeps_non_whitelisted_assets_record_only(tmp_path):
    _seed_templates(tmp_path)
    original = "rules:\n  min_score: 0.42\n"
    target_path = tmp_path / "templates" / "filter-rules.example.yaml"
    _write_text(target_path, original)
    proposal = propose_evolution(
        tmp_path,
        reflection_type="OPTIMIZATION",
        target_asset="templates/filter-rules.example.yaml",
        rationale="This asset is intentionally outside the whitelist.",
        proposed_change={"rules": {"min_score": 0.55}},
        evidence=["_runs/feedback.jsonl#2"],
    )

    activated = activate_evolution(tmp_path, proposal["id"], approved=True)

    assert activated["status"] == "active"
    assert activated["asset_application"]["status"] == "record_only"
    assert target_path.read_text(encoding="utf-8") == original


def test_activate_evolution_records_backup_and_rollback_metadata(tmp_path):
    _seed_templates(tmp_path)
    target_path = tmp_path / "templates" / "ranking.example.yaml"
    original = target_path.read_text(encoding="utf-8")
    proposal = propose_evolution(
        tmp_path,
        reflection_type="OPTIMIZATION",
        target_asset="templates/ranking.example.yaml",
        rationale="Track rollback metadata for applied template changes.",
        proposed_change={"weights": {"topic_relevance": 0.33}},
        evidence=["_runs/feedback.jsonl#3"],
    )

    activated = activate_evolution(tmp_path, proposal["id"], approved=True)
    active_record = _read_json(tmp_path / "_evolution" / "active" / f"{proposal['id']}.json")

    backup_path = Path(active_record["rollback"]["backup_path"])
    assert activated["asset_application"]["backup_created"] is True
    assert active_record["rollback"]["target_asset"] == "templates/ranking.example.yaml"
    assert backup_path.is_file()
    assert backup_path.read_text(encoding="utf-8") == original
