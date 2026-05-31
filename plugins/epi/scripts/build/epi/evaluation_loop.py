from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from epi.artifacts import utc_now, write_json_atomic, write_text_atomic


SCHEMA_VERSION = "epi-improvement-brief-v1"
QUALITY_LOOP_STEPS = [
    "plugin-eval",
    "epi-quality-gates",
    "benchmark",
    "compare-before-after",
    "improvement-brief",
    "skill-aware-evolve-proposal",
]
REQUIRED_QUALITY_SOURCES = ["plugin_eval", "epi_quality_gates", "benchmark"]
NON_REGRESSION_METRICS = [
    "plugin_eval_score",
    "coverage_percent",
    "epi-quality-gate-pass-rate",
    "benchmark_pass_rate",
]


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _coerce_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _normalize_metric_name(name: str) -> str:
    return name.strip().replace(" ", "_")


def _collect_metric(metrics: dict[str, Any], name: str, value: Any) -> None:
    number = _coerce_number(value)
    if number is not None:
        metrics[_normalize_metric_name(name)] = number


def extract_metrics(payload: dict[str, Any], *, source_kind: str = "generic") -> dict[str, float]:
    metrics: dict[str, float] = {}
    if not payload:
        return metrics

    for key in ["plugin_eval_score", "coverage_percent", "benchmark_pass_rate"]:
        if key in payload:
            _collect_metric(metrics, key, payload[key])

    if source_kind == "plugin_eval":
        for key in ["score", "overall_score"]:
            if key in payload:
                _collect_metric(metrics, "plugin_eval_score", payload[key])
        summary = payload.get("summary")
        if isinstance(summary, dict):
            for key in ["score", "overall_score"]:
                if key in summary:
                    _collect_metric(metrics, "plugin_eval_score", summary[key])

    nested_metrics = payload.get("metrics")
    if isinstance(nested_metrics, dict):
        for key, value in nested_metrics.items():
            _collect_metric(metrics, str(key), value)
    elif isinstance(nested_metrics, list):
        for item in nested_metrics:
            if not isinstance(item, dict):
                continue
            metric_id = item.get("id") or item.get("name") or item.get("metric")
            if metric_id:
                _collect_metric(metrics, str(metric_id), item.get("value"))

    cases = payload.get("cases")
    if isinstance(cases, list) and cases:
        passed = 0
        total = 0
        for case in cases:
            if not isinstance(case, dict):
                continue
            total += 1
            if case.get("passed") is True or case.get("status") == "pass":
                passed += 1
        if total:
            metrics.setdefault("benchmark_pass_rate", round(passed / total, 4))

    return metrics


def _merge_metrics(*metric_groups: dict[str, Any] | None) -> dict[str, float]:
    merged: dict[str, float] = {}
    for group in metric_groups:
        if not group:
            continue
        for key, value in group.items():
            _collect_metric(merged, str(key), value)
    return merged


def _metric_comparisons(before_metrics: dict[str, float], after_metrics: dict[str, float]) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    for metric in sorted(set(before_metrics) & set(after_metrics)):
        before = before_metrics[metric]
        after = after_metrics[metric]
        delta = round(after - before, 6)
        if delta > 0:
            trend = "improved"
        elif delta < 0:
            trend = "regressed"
        else:
            trend = "unchanged"
        comparisons.append(
            {
                "metric": metric,
                "before": before,
                "after": after,
                "delta": delta,
                "trend": trend,
                "assumption": "higher_is_better",
            }
        )
    return comparisons


def _gate_id(metric: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]+", "_", metric).strip("_").lower()
    return f"{safe}_non_regression"


def default_acceptance_gates(before_metrics: dict[str, float]) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = [{"id": "human_approval", "required": True}]
    for metric in NON_REGRESSION_METRICS:
        if metric in before_metrics:
            gates.append(
                {
                    "id": _gate_id(metric),
                    "metric": metric,
                    "operator": ">=",
                    "value": before_metrics[metric],
                    "required": True,
                }
            )
    return gates


def _source_record(path: Path | None, source_kind: str) -> dict[str, Any]:
    payload = _read_json(path)
    return {
        "kind": source_kind,
        "path": str(path) if path else None,
        "present": bool(path and path.exists()),
        "metrics": extract_metrics(payload, source_kind=source_kind),
    }


def _source_completeness(sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    missing_sources = [
        source_name
        for source_name in REQUIRED_QUALITY_SOURCES
        if not sources.get(source_name, {}).get("present")
    ]
    return {
        "required_sources": REQUIRED_QUALITY_SOURCES,
        "present_sources": [
            source_name
            for source_name in REQUIRED_QUALITY_SOURCES
            if sources.get(source_name, {}).get("present")
        ],
        "missing_sources": missing_sources,
        "complete": not missing_sources,
    }


def build_improvement_brief(
    *,
    target_asset: str,
    rationale: str,
    proposed_change: dict[str, Any],
    before_metrics: dict[str, Any] | None = None,
    after_metrics: dict[str, Any] | None = None,
    plugin_eval_path: Path | None = None,
    metric_pack_path: Path | None = None,
    benchmark_path: Path | None = None,
    evidence: list[str] | None = None,
    reflection_type: str = "OPTIMIZATION",
    evidence_type: str = "plugin_eval_warning",
    brief_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(proposed_change, dict) or not proposed_change:
        raise ValueError("proposed_change must be a non-empty object")

    sources = {
        "plugin_eval": _source_record(plugin_eval_path, "plugin_eval"),
        "epi_quality_gates": _source_record(metric_pack_path, "metric_pack"),
        "benchmark": _source_record(benchmark_path, "benchmark"),
    }
    before = _merge_metrics(before_metrics)
    after = _merge_metrics(
        sources["plugin_eval"]["metrics"],
        sources["epi_quality_gates"]["metrics"],
        sources["benchmark"]["metrics"],
        after_metrics,
    )
    evidence_items = list(evidence or [])
    for source in sources.values():
        if source["present"]:
            evidence_items.append(source["path"])

    source_completeness = _source_completeness(sources)
    gates = default_acceptance_gates(before)
    if not source_completeness["complete"]:
        gates.append(
            {
                "id": "quality_loop_sources_complete",
                "required": True,
                "status": "missing",
                "missing_sources": source_completeness["missing_sources"],
            }
        )
    comparisons = _metric_comparisons(before, after)
    next_action = (
        "propose-evolution"
        if source_completeness["complete"]
        else "collect-missing-quality-evidence"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "id": brief_id or f"brief-{uuid.uuid4().hex[:12]}",
        "created_at": utc_now(),
        "quality_loop": QUALITY_LOOP_STEPS,
        "target_asset": target_asset,
        "rationale": rationale,
        "proposed_change": proposed_change,
        "sources": sources,
        "source_completeness": source_completeness,
        "before_metrics": before,
        "after_metrics": after,
        "metric_comparisons": comparisons,
        "improvement_summary": {
            "regressed_metrics": [
                item["metric"] for item in comparisons if item["trend"] == "regressed"
            ],
            "improved_metrics": [
                item["metric"] for item in comparisons if item["trend"] == "improved"
            ],
            "next_action": next_action,
        },
        "proposed_evolution": {
            "reflection_type": reflection_type,
            "evidence_type": evidence_type,
            "target_asset": target_asset,
            "rationale": rationale,
            "proposed_change": proposed_change,
            "evidence": evidence_items,
            "before_metrics": before,
            "acceptance_gates": gates,
        },
    }


def render_improvement_brief(brief: dict[str, Any]) -> str:
    lines = [
        f"# EPI Improvement Brief - {brief.get('id')}",
        "",
        f"schema_version: {brief.get('schema_version')}",
        f"target_asset: {brief.get('target_asset')}",
        f"next_action: {brief.get('improvement_summary', {}).get('next_action')}",
        "",
        "## Quality Loop",
        "",
    ]
    lines.extend(f"- {step}" for step in brief.get("quality_loop", []))
    completeness = brief.get("source_completeness") or {}
    lines.extend(["", "## Source Completeness", ""])
    lines.append(f"- complete: {completeness.get('complete')}")
    missing_sources = completeness.get("missing_sources") or []
    if missing_sources:
        lines.append(f"- missing_sources: {', '.join(missing_sources)}")
    else:
        lines.append("- missing_sources: none")
    lines.extend(["", "## Metric Comparison", ""])
    comparisons = brief.get("metric_comparisons") or []
    if comparisons:
        lines.append("| Metric | Before | After | Delta | Trend |")
        lines.append("| --- | ---: | ---: | ---: | --- |")
        for item in comparisons:
            lines.append(
                f"| {item['metric']} | {item['before']} | {item['after']} | {item['delta']} | {item['trend']} |"
            )
    else:
        lines.append("- No comparable before/after metrics were provided.")
    lines.extend(["", "## Proposed Evolution", ""])
    proposed = brief.get("proposed_evolution") or {}
    lines.append(f"- reflection_type: {proposed.get('reflection_type')}")
    lines.append(f"- evidence_type: {proposed.get('evidence_type')}")
    lines.append(f"- target_asset: {proposed.get('target_asset')}")
    lines.append(f"- rationale: {brief.get('rationale')}")
    lines.append("- acceptance_gates:")
    for gate in proposed.get("acceptance_gates") or []:
        metric = gate.get("metric")
        if metric:
            lines.append(f"  - {gate.get('id')}: {metric} {gate.get('operator')} {gate.get('value')}")
        else:
            lines.append(f"  - {gate.get('id')}")
    lines.append("")
    return "\n".join(lines)


def write_improvement_brief(output_dir: Path, brief: dict[str, Any]) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{brief['id']}.json"
    markdown_path = output_dir / f"{brief['id']}.md"
    write_json_atomic(json_path, brief)
    write_text_atomic(markdown_path, render_improvement_brief(brief))
    return {
        "json": str(json_path),
        "markdown": str(markdown_path),
    }
