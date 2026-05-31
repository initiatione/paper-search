from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

from epi.artifacts import file_sha256, raw_paper_root, staging_paper_root, utc_now, write_json_atomic
from epi.paper_gate import build_paper_gate


_INTERNAL_VAULT_ROOTS = {"_raw", "_staging", "_runs", "_quarantine", ".git", ".obsidian"}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _gate_check_names(gate: dict[str, Any], conclusion: str) -> list[str]:
    return [
        str(run.get("name"))
        for run in gate.get("check_suite", {}).get("check_runs", [])
        if run.get("conclusion") == conclusion
    ]


def _ensure_gate_allows_record(gate: dict[str, Any]) -> None:
    failure_checks = _gate_check_names(gate, "failure")
    if failure_checks:
        raise ValueError("paper gate has failure checks: " + ", ".join(failure_checks))

    next_action = gate.get("next_action")
    if next_action not in {"run-wiki-ingest-agent", "review-recorded-wiki-pages"}:
        raise ValueError(
            "record-wiki-ingest requires paper-gate next_action=run-wiki-ingest-agent; "
            f"got {next_action or 'unknown'}"
        )

    action_required = _gate_check_names(gate, "action_required")
    unresolved = [name for name in action_required if name != "human-approval"]
    if unresolved:
        raise ValueError("paper gate has unresolved action-required checks: " + ", ".join(unresolved))


def _is_agent_mediated_plan(plan: dict[str, Any]) -> bool:
    return (
        plan.get("handoff_type") == "agent-mediated-wiki-ingest"
        or plan.get("wiki_write_model") == "agent-mediated-vault-contract"
    )


def _resolve_page(vault_path: Path, page: str) -> dict[str, Any]:
    value = str(page or "").strip()
    if not value:
        raise ValueError("page path must not be empty")

    normalized = value.replace("\\", "/")
    parsed = PurePosixPath(normalized)
    if ".." in parsed.parts:
        raise ValueError(f"page path must not contain '..': {page}")

    candidate = Path(value)
    resolved = candidate.resolve() if candidate.is_absolute() else (vault_path / candidate).resolve()
    try:
        relative_path = resolved.relative_to(vault_path)
    except ValueError as exc:
        raise ValueError(f"page path must stay inside vault: {page}") from exc

    if not relative_path.parts:
        raise ValueError("page path must point to a file inside the vault")
    if relative_path.parts[0] in _INTERNAL_VAULT_ROOTS:
        raise ValueError(f"recorded final wiki page must not be under {relative_path.parts[0]}: {page}")
    if resolved.suffix.lower() != ".md":
        raise ValueError(f"recorded final wiki page must be a Markdown file: {page}")
    if not resolved.is_file():
        raise FileNotFoundError(f"recorded final wiki page does not exist: {resolved}")

    return {
        "path": str(resolved),
        "relative_path": relative_path.as_posix(),
        "sha256": file_sha256(resolved),
        "size_bytes": resolved.stat().st_size,
    }


def _source_first_confirmed(brief: dict[str, Any]) -> bool:
    source_bundle = brief.get("source_bundle") if isinstance(brief.get("source_bundle"), dict) else {}
    raw_artifacts = "\n".join(str(item) for item in source_bundle.get("raw_artifacts") or [])
    formula_figure_review = (
        source_bundle.get("formula_figure_review")
        if isinstance(source_bundle.get("formula_figure_review"), dict)
        else {}
    )
    formula_figure_text = "\n".join(str(item) for item in formula_figure_review.values()).lower()
    return all(
        artifact in raw_artifacts
        for artifact in [
            "mineru/paper.md",
            "mineru/paper.tex",
            "mineru/images/*",
            "mineru/mineru-manifest.json",
        ]
    ) and all(token in formula_figure_text for token in ["formula", "figure", "image"])


def create_wiki_ingest_record(
    vault_path: Path,
    slug: str,
    pages: list[str],
    *,
    approved_by: str,
    notes: str | None = None,
) -> dict[str, Any]:
    vault_path = vault_path.resolve()
    if not str(approved_by or "").strip():
        raise ValueError("human gate approval is required for record-wiki-ingest")
    if not pages:
        raise ValueError("at least one final wiki page must be recorded")

    paper_root = raw_paper_root(vault_path, slug)
    staging_root = staging_paper_root(vault_path, slug)
    plan_path = staging_root / "promotion-plan.json"
    plan = _read_json(plan_path)
    if not plan:
        raise FileNotFoundError(f"missing promotion plan: {plan_path}")
    if not _is_agent_mediated_plan(plan):
        raise ValueError("record-wiki-ingest only supports agent-mediated wiki ingest plans")

    brief_path = Path(plan.get("wiki_ingest_brief_path") or staging_root / "wiki-ingest-brief.json")
    brief = _read_json(brief_path)
    if not brief:
        raise FileNotFoundError(f"missing wiki ingest brief: {brief_path}")

    gate = build_paper_gate(vault_path, slug)
    _ensure_gate_allows_record(gate)

    page_records = [_resolve_page(vault_path, page) for page in pages]
    seen: set[str] = set()
    duplicates = []
    for record in page_records:
        relative = record["relative_path"]
        if relative in seen:
            duplicates.append(relative)
        seen.add(relative)
    if duplicates:
        raise ValueError("duplicate final wiki page records: " + ", ".join(duplicates))

    recorded_at = utc_now()
    failure_checks = _gate_check_names(gate, "failure")
    action_required_checks = _gate_check_names(gate, "action_required")
    human_gate_decision = {
        "status": "approved",
        "approved_by": str(approved_by).strip(),
        "approved_at": recorded_at,
        "approval_scope": "agent-mediated-final-wiki-ingest-record",
    }
    if notes:
        human_gate_decision["notes"] = notes

    record_payload = {
        "schema_version": "epi-wiki-ingest-record-v1",
        "stage": "record-wiki-ingest",
        "status": "recorded",
        "paper_slug": slug,
        "title": brief.get("title") or gate.get("title") or slug,
        "recorded_at": recorded_at,
        "vault_path": str(vault_path),
        "compiled_wiki_write": False,
        "record_only": True,
        "final_pages_modified_by_epi": False,
        "wiki_write_model": plan.get("wiki_write_model") or "agent-mediated-vault-contract",
        "handoff_type": plan.get("handoff_type") or brief.get("handoff_type"),
        "final_page_authority": plan.get("final_page_authority"),
        "source_first_confirmed": _source_first_confirmed(brief),
        "human_gate_decision": human_gate_decision,
        "paper_gate": {
            "status": gate.get("status"),
            "next_action": gate.get("next_action"),
            "conclusion": gate.get("check_suite", {}).get("conclusion"),
            "failure_checks": failure_checks,
            "action_required_checks": action_required_checks,
        },
        "paths": {
            "paper_root": str(paper_root),
            "staging_root": str(staging_root),
            "promotion_plan": str(plan_path),
            "wiki_ingest_brief": str(brief_path),
            "agent_handoff_paths": plan.get("agent_handoff_paths") or [],
        },
        "page_records": page_records,
        "page_paths": [record["path"] for record in page_records],
        "relative_page_paths": [record["relative_path"] for record in page_records],
        "ingest_policy": brief.get("ingest_policy") if isinstance(brief.get("ingest_policy"), dict) else {},
        "source_bundle": brief.get("source_bundle") if isinstance(brief.get("source_bundle"), dict) else {},
        "wiki_rule_source_model": (
            brief.get("wiki_rule_source_model")
            if isinstance(brief.get("wiki_rule_source_model"), dict)
            else {}
        ),
    }
    if notes:
        record_payload["notes"] = notes

    raw_record_path = paper_root / "wiki-ingest-record.json"
    staging_record_path = staging_root / "wiki-ingest-record.json"
    record_payload["record_paths"] = {
        "raw": str(raw_record_path),
        "staging": str(staging_record_path),
    }
    write_json_atomic(raw_record_path, record_payload)
    write_json_atomic(staging_record_path, record_payload)
    return record_payload
