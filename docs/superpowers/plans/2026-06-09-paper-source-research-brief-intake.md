# Paper Source Research Brief Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Paper Source-native Research Brief intake path: `research-grill-me` creates managed Research Brief artifacts, `research-brief` manages them, and `dry-run --from-brief` consumes them.

**Architecture:** Keep Research Brief artifact logic in one focused runtime module and keep CLI/orchestrator layers thin. Query planning consumes structured brief fields deterministically; it must not render the brief to one freeform query string. Skill docs own conversation behavior and route users toward the CLI artifact manager without crossing the Paper Wiki handoff boundary.

**Tech Stack:** Python stdlib, existing Paper Source runtime modules, pytest, Paper Source skill bundle metadata.

---

## File Structure

- Create `plugins/paper-source/scripts/build/paper_source/research_brief.py`: schema constants, slug validation, create/validate/list helpers, markdown rendering, hash metadata, and formal-use checks.
- Modify `plugins/paper-source/scripts/build/paper_source/query_planner.py`: add deterministic `build_query_plan_from_research_brief(...)` wrapper that maps Research Brief fields plus profile fill into the existing plan shape.
- Modify `plugins/paper-source/scripts/build/paper_source/cli_parser.py`: add `research-brief` subcommands and `dry-run --from-brief` / `--allow-draft-brief` parser options.
- Modify `plugins/paper-source/scripts/build/paper_source/cli_routes.py`: register `research-brief`.
- Modify `plugins/paper-source/scripts/build/paper_source/cli.py`: add thin handlers for `research-brief` and pass brief options into `run_dry_run`.
- Modify `plugins/paper-source/scripts/build/paper_source/orchestrator.py`: load brief for dry-run, record brief metadata in run state/report/search record, include brief hash in review-session signature, and print concise context reminder through CLI payloads.
- Modify `plugins/paper-source/scripts/build/paper_source/review_sessions.py` only if signature cleaning drops brief metadata incorrectly; preferred path is to pass stable brief metadata through existing `build_review_signature`.
- Modify `plugins/paper-source/scripts/build/paper_source/report_run.py` only if dry-run report rendering needs explicit Research Brief lines not already present through `discovery_context`.
- Create `plugins/paper-source/skills/research-grill-me/SKILL.md`: concise one-question-at-a-time entrypoint.
- Create `plugins/paper-source/skills/research-grill-me/references/research-brief-contract.md`: schema, status, precedence, Paper Wiki boundary.
- Create `plugins/paper-source/skills/research-grill-me/agents/openai.yaml`: UI metadata.
- Modify `plugins/paper-source/skills/routing.yaml`: add primary `research_grill_me` route.
- Add focused tests:
  - `tests/paper_source/test_research_brief.py`
  - `tests/paper_source/test_research_brief_cli.py`
  - `tests/paper_source/test_dry_run_from_brief.py`
  - `tests/paper_source/test_research_grill_skill_contract.py`
- Update adjacent tests:
  - `tests/paper_source/test_cli_parser.py`
  - `tests/paper_source/test_paper_discovery_query_planner.py`
  - `tests/paper_source/test_orchestrator_dry_run.py`
  - `tests/paper_source/test_config_onboarding_docs.py`
  - `plugins/paper-source/tests/test_skill_bundle_contract.py`

## Behavior Contracts

- Research Brief directory: `_paper_source/research-briefs/YYYYMMDD-<short-topic-slug>/`.
- Required files: `research-brief.json`, `research-brief.md`, `agent-brief.md`, `revisions/`.
- Slug format: lowercase ASCII kebab-case prefixed by eight digits and a hyphen.
- Status values: `draft`, `confirmed`, `superseded`.
- Formal `dry-run --from-brief` default accepts only `confirmed`.
- Draft brief use requires `--allow-draft-brief`, must be recorded in run state, and must be visible in output.
- `--query` and `--from-brief` are mutually exclusive.
- `dry-run --query` remains a quick path.
- `Research Brief > Research Profile`; profile fills missing values only.
- No Research Brief path may trigger Paper Wiki formal pages directly.

## Task 1: Research Brief Artifact Module

**Files:**
- Create: `plugins/paper-source/scripts/build/paper_source/research_brief.py`
- Create: `tests/paper_source/test_research_brief.py`

- [ ] **Step 1: Write failing tests for artifact creation and validation**

Add tests that assert:

```python
from __future__ import annotations

import json

import pytest

from paper_source.research_brief import (
    ResearchBriefValidationError,
    create_research_brief,
    load_research_brief,
    validate_research_brief_payload,
)


def _answers(slug="20260609-auv-current-disturbance-control", status="confirmed"):
    return {
        "status": status,
        "slug": slug,
        "title": "AUV强海流扰动控制",
        "task": "Find high-quality recent papers on AUV control under strong current disturbances.",
        "domain_scope": "AUV trajectory tracking and disturbance rejection with ocean current anchors.",
        "specific_questions": ["Which methods report real or high-fidelity current disturbance evaluation?"],
        "keywords": ["AUV", "ocean current", "disturbance rejection", "trajectory tracking"],
        "exclusions": ["acoustic communication"],
        "review_policy": {"type": "exclude"},
        "source_scope": {"type": "paper_search_mcp_default", "notes": ""},
        "output_goal": {"type": "reading_priority_list", "notes": ""},
        "unknowns": ["venue_prior"],
        "field_sources": {
            "task": "user_confirmed",
            "domain_scope": "user_confirmed",
            "review_policy.type": "brief_default",
            "output_goal.type": "user_confirmed",
        },
    }


def test_create_research_brief_writes_managed_artifacts(tmp_path):
    result = create_research_brief(tmp_path, _answers(), now="2026-06-09T12:00:00Z")

    brief_dir = tmp_path / "_paper_source" / "research-briefs" / "20260609-auv-current-disturbance-control"
    assert result["brief_dir"] == str(brief_dir)
    assert (brief_dir / "research-brief.json").exists()
    assert (brief_dir / "research-brief.md").read_text(encoding="utf-8").startswith("# AUV强海流扰动控制")
    assert "Research Brief" in (brief_dir / "agent-brief.md").read_text(encoding="utf-8")
    assert (brief_dir / "revisions").is_dir()

    payload = json.loads((brief_dir / "research-brief.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == "paper-source-research-brief-v1"
    assert payload["revision_number"] == 1
    assert payload["status"] == "confirmed"
    assert payload["created_at"] == "2026-06-09T12:00:00Z"
    assert result["hash"] == payload["content_hash"]


def test_slug_validation_rejects_unsafe_names(tmp_path):
    with pytest.raises(ResearchBriefValidationError, match="slug"):
        create_research_brief(tmp_path, _answers(slug="../bad"), now="2026-06-09T12:00:00Z")


def test_validate_requires_minimum_complete_fields():
    payload = _answers()
    payload["task"] = ""
    with pytest.raises(ResearchBriefValidationError, match="task"):
        validate_research_brief_payload(payload)


def test_draft_is_valid_but_not_formal_use_eligible(tmp_path):
    result = create_research_brief(tmp_path, _answers(status="draft"), now="2026-06-09T12:00:00Z")
    loaded = load_research_brief(result["json_path"])
    assert loaded["payload"]["status"] == "draft"
    assert loaded["formal_use_eligible"] is False
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests\paper_source\test_research_brief.py -q
```

Expected: fails with `ModuleNotFoundError: No module named 'paper_source.research_brief'`.

- [ ] **Step 3: Implement minimal artifact module**

Implement:

```python
SCHEMA_VERSION = "paper-source-research-brief-v1"
STATUS_VALUES = {"draft", "confirmed", "superseded"}
REVIEW_POLICY_VALUES = {"exclude", "include", "mixed"}
OUTPUT_GOAL_VALUES = {
    "reading_priority_list",
    "source_staging_candidates",
    "literature_review_seed",
    "topic_tracking_seed",
    "fact_check_sources",
}
SOURCE_SCOPE_VALUES = {
    "paper_search_mcp_default",
    "paper_search_mcp_oa_priority",
    "known_paper_lookup",
    "venue_or_publisher_targeted",
    "manual_sources_provided",
}
```

Add helpers:

```python
def research_briefs_root(vault_path: Path) -> Path
def validate_slug(slug: str) -> str
def validate_research_brief_payload(payload: dict[str, Any], *, formal_use: bool = False) -> dict[str, Any]
def create_research_brief(vault_path: Path, answers: dict[str, Any], *, now: str | None = None) -> dict[str, Any]
def load_research_brief(path: Path, *, allow_draft: bool = False) -> dict[str, Any]
def research_brief_metadata(path: Path, payload: dict[str, Any]) -> dict[str, Any]
```

Use `paper_source.artifacts.write_json_atomic`, `paper_source.artifacts.json_sha256`, and `paper_source.artifacts.utc_now`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```powershell
python -m pytest tests\paper_source\test_research_brief.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Add revision snapshot behavior**

Extend tests:

```python
from paper_source.research_brief import revise_research_brief


def test_confirmed_revision_preserves_prior_json_snapshot(tmp_path):
    created = create_research_brief(tmp_path, _answers(), now="2026-06-09T12:00:00Z")
    revised = _answers()
    revised["task"] = "Find AUV current-disturbance control papers with field trials."

    result = revise_research_brief(created["json_path"], revised, now="2026-06-09T13:00:00Z")

    payload = json.loads((tmp_path / "_paper_source" / "research-briefs" / revised["slug"] / "research-brief.json").read_text(encoding="utf-8"))
    snapshots = sorted((tmp_path / "_paper_source" / "research-briefs" / revised["slug"] / "revisions").glob("*-research-brief.json"))
    assert payload["revision_number"] == 2
    assert payload["supersedes_hash"] == created["hash"]
    assert len(snapshots) == 1
```

Implement `revise_research_brief(path, answers, *, now=None)`.

- [ ] **Step 6: Re-run focused tests and commit**

Run:

```powershell
python -m pytest tests\paper_source\test_research_brief.py -q
git add plugins\paper-source\scripts\build\paper_source\research_brief.py tests\paper_source\test_research_brief.py
git commit -m "feat: add research brief artifacts"
```

## Task 2: Research Brief CLI

**Files:**
- Modify: `plugins/paper-source/scripts/build/paper_source/cli_parser.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/cli_routes.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/cli.py`
- Create: `tests/paper_source/test_research_brief_cli.py`
- Modify: `tests/paper_source/test_cli_parser.py`

- [ ] **Step 1: Write failing parser and CLI tests**

Add tests that assert:

```python
from __future__ import annotations

import json

import pytest

from paper_source.cli_parser import build_parser
from paper_source import cli


def _answers():
    return {
        "status": "confirmed",
        "slug": "20260609-auv-current-disturbance-control",
        "title": "AUV强海流扰动控制",
        "task": "Find high-quality recent papers on AUV control under strong current disturbances.",
        "domain_scope": "AUV trajectory tracking and disturbance rejection with ocean current anchors.",
        "keywords": ["AUV", "ocean current"],
        "review_policy": {"type": "exclude"},
        "source_scope": {"type": "paper_search_mcp_default", "notes": ""},
        "output_goal": {"type": "reading_priority_list", "notes": ""},
        "field_sources": {
            "task": "user_confirmed",
            "domain_scope": "user_confirmed",
            "review_policy.type": "brief_default",
            "output_goal.type": "user_confirmed",
        },
    }


def test_research_brief_parser_accepts_create_validate_list(tmp_path):
    parser = build_parser()
    create = parser.parse_args(["research-brief", "create", "--answers-json", str(tmp_path / "answers.json"), "--vault", str(tmp_path)])
    assert create.command == "research-brief"
    assert create.research_brief_action == "create"

    validate = parser.parse_args(["research-brief", "validate", "--brief", str(tmp_path / "brief.json"), "--json"])
    assert validate.research_brief_action == "validate"
    assert validate.json is True

    listed = parser.parse_args(["research-brief", "list", "--vault", str(tmp_path), "--json"])
    assert listed.research_brief_action == "list"


def test_research_brief_create_and_list_json(tmp_path, capsys):
    answers_path = tmp_path / "answers.json"
    answers_path.write_text(json.dumps(_answers(), ensure_ascii=False), encoding="utf-8")

    assert cli.main(["research-brief", "create", "--answers-json", str(answers_path), "--vault", str(tmp_path), "--json"]) == 0
    created = json.loads(capsys.readouterr().out)
    assert created["brief_slug"] == "20260609-auv-current-disturbance-control"
    assert created["artifacts"]["json"].endswith("research-brief.json")

    assert cli.main(["research-brief", "list", "--vault", str(tmp_path), "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["briefs"][0]["brief_slug"] == "20260609-auv-current-disturbance-control"
    assert "keywords" not in listed["briefs"][0]


def test_research_brief_validate_rejects_invalid_payload(tmp_path, capsys):
    invalid = tmp_path / "bad.json"
    invalid.write_text("{}", encoding="utf-8")
    assert cli.main(["research-brief", "validate", "--brief", str(invalid), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
```

Update `tests/paper_source/test_cli_parser.py::test_cli_parser_commands_match_routes` only if the route drift check needs a new command.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests\paper_source\test_research_brief_cli.py tests\paper_source\test_cli_parser.py::test_cli_parser_commands_match_routes -q
```

Expected: parser rejects `research-brief`.

- [ ] **Step 3: Add parser/routes/handlers**

Parser shape:

```python
research_brief = subparsers.add_parser("research-brief")
research_brief_subparsers = research_brief.add_subparsers(dest="research_brief_action", required=True)
research_brief_create = research_brief_subparsers.add_parser("create")
research_brief_create.add_argument("--answers-json", type=Path, required=True)
_add_common_vault(research_brief_create)
research_brief_create.add_argument("--json", action="store_true")
research_brief_validate = research_brief_subparsers.add_parser("validate")
research_brief_validate.add_argument("--brief", type=Path, required=True)
research_brief_validate.add_argument("--json", action="store_true")
research_brief_list = research_brief_subparsers.add_parser("list")
_add_common_vault(research_brief_list)
research_brief_list.add_argument("--json", action="store_true")
```

Route:

```python
"research-brief": "_handle_research_brief",
```

Handler:

```python
def _handle_research_brief(args: argparse.Namespace) -> int:
    if args.research_brief_action == "create":
        ...
    if args.research_brief_action == "validate":
        ...
    if args.research_brief_action == "list":
        ...
    raise ValueError(...)
```

Use `paper_source.research_brief.create_research_brief`, `validate_research_brief_file`, and `list_research_briefs`.

- [ ] **Step 4: Run tests to verify GREEN**

Run:

```powershell
python -m pytest tests\paper_source\test_research_brief_cli.py tests\paper_source\test_cli_parser.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

Run:

```powershell
git add plugins\paper-source\scripts\build\paper_source\cli_parser.py plugins\paper-source\scripts\build\paper_source\cli_routes.py plugins\paper-source\scripts\build\paper_source\cli.py tests\paper_source\test_research_brief_cli.py tests\paper_source\test_cli_parser.py
git commit -m "feat: add research brief CLI"
```

## Task 3: Dry-Run From Brief Integration

**Files:**
- Modify: `plugins/paper-source/scripts/build/paper_source/cli_parser.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/cli.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/orchestrator.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/query_planner.py`
- Modify if needed: `plugins/paper-source/scripts/build/paper_source/report_run.py`
- Create: `tests/paper_source/test_dry_run_from_brief.py`
- Modify: `tests/paper_source/test_paper_discovery_query_planner.py`
- Modify: `tests/paper_source/test_orchestrator_dry_run.py`

- [ ] **Step 1: Write failing parser tests for mutual exclusivity**

Add:

```python
def test_dry_run_parser_accepts_from_brief_and_rejects_query_mix(tmp_path):
    parser = build_parser()
    args = parser.parse_args(["dry-run", "--from-brief", str(tmp_path / "research-brief.json"), "--vault", str(tmp_path)])
    assert args.from_brief == tmp_path / "research-brief.json"
    assert args.query is None

    with pytest.raises(SystemExit):
        parser.parse_args(["dry-run", "--query", "AUV control", "--from-brief", str(tmp_path / "research-brief.json")])
```

Expected parser implementation: replace required `--query` with a mutually exclusive group:

```python
query_input = dry_run.add_mutually_exclusive_group(required=True)
query_input.add_argument("--query", default=None)
query_input.add_argument("--from-brief", type=Path, default=None)
dry_run.add_argument("--allow-draft-brief", action="store_true")
```

- [ ] **Step 2: Write failing query planner tests**

Add:

```python
from paper_source.query_planner import build_query_plan_from_research_brief


def test_query_planner_maps_research_brief_as_hard_current_intent():
    brief = {
        "task": "Find papers on aircraft control reviews",
        "domain_scope": "fixed-wing aircraft fault-tolerant control",
        "specific_questions": ["Which papers compare real flight experiments?"],
        "keywords": ["fault-tolerant control", "flight experiment"],
        "exclusions": ["AUV"],
        "review_policy": {"type": "include"},
        "source_scope": {"type": "paper_search_mcp_default"},
        "output_goal": {"type": "literature_review_seed"},
    }
    plan = build_query_plan_from_research_brief(
        brief,
        profile="auv_control",
        domains=["AUV", "underwater robot"],
        positive_keywords=["ocean current"],
        negative_keywords=["acoustic communication"],
        venue_prior=[],
        max_queries=4,
    )
    assert plan["topic"] == "Find papers on aircraft control reviews"
    assert plan["domain"] == "research-brief"
    assert "fixed-wing aircraft fault-tolerant control" in plan["concept_blocks"]["domain_terms"]
    assert "AUV" in plan["concept_blocks"]["exclusions"]
    assert all("-review -survey" not in query for query in plan["query_variants"])
    assert plan["research_brief"]["output_goal"] == "literature_review_seed"
```

- [ ] **Step 3: Write failing dry-run integration tests**

Use existing dry-run fixture patterns from `tests/paper_source/test_orchestrator_dry_run.py`. Add tests that:

```python
from paper_source.orchestrator import run_dry_run
from paper_source.research_brief import create_research_brief


def test_dry_run_from_confirmed_brief_records_metadata_and_hash(tmp_path, monkeypatch):
    brief = create_research_brief(tmp_path, _answers(), now="2026-06-09T12:00:00Z")
    fixture = _write_search_fixture(tmp_path)
    run_dir = run_dry_run(
        plugin_root=PLUGIN_ROOT,
        vault_path=tmp_path,
        query=None,
        from_brief=brief["json_path"],
        max_results=3,
        fixture_path=fixture,
        use_query_plan=True,
        resume=False,
    )
    state = json.loads((run_dir / "run-state.json").read_text(encoding="utf-8"))
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    assert state["research_brief"]["slug"] == "20260609-auv-current-disturbance-control"
    assert state["research_brief"]["hash"] == brief["hash"]
    assert report["discovery_context"]["research_brief"]["revision_number"] == 1


def test_dry_run_from_draft_brief_requires_override(tmp_path):
    brief = create_research_brief(tmp_path, _answers(status="draft"), now="2026-06-09T12:00:00Z")
    with pytest.raises(ValueError, match="draft"):
        run_dry_run(plugin_root=PLUGIN_ROOT, vault_path=tmp_path, query=None, from_brief=brief["json_path"], use_query_plan=True)


def test_brief_hash_changes_review_signature(tmp_path):
    first = create_research_brief(tmp_path, _answers(slug="20260609-auv-current-disturbance-control"), now="2026-06-09T12:00:00Z")
    second_answers = _answers(slug="20260609-auv-current-disturbance-control-v2")
    second_answers["task"] = "Find AUV current disturbance papers with sea trials."
    second = create_research_brief(tmp_path, second_answers, now="2026-06-09T13:00:00Z")
    first_signature = _dry_run_signature_for_test(tmp_path, first["json_path"])
    second_signature = _dry_run_signature_for_test(tmp_path, second["json_path"])
    assert first_signature != second_signature
```

- [ ] **Step 4: Run tests to verify RED**

Run:

```powershell
python -m pytest tests\paper_source\test_dry_run_from_brief.py tests\paper_source\test_paper_discovery_query_planner.py -q
```

Expected: missing `from_brief` support and missing planner wrapper.

- [ ] **Step 5: Implement deterministic planner mapping**

Add `build_query_plan_from_research_brief(...)` that:

- sets `domain` to `research-brief`;
- uses `task` as topic;
- inserts `domain_scope` into `concept_blocks.domain_terms` before profile terms;
- inserts `keywords` and `specific_questions` into method/topic/problem terms;
- appends `exclusions`;
- maps `review_policy.type == "exclude"` to non-review exclusion suffixes;
- maps `review_policy.type in {"include", "mixed"}` to not forcing `-review -survey`;
- records a compact `research_brief` block with `slug`, `status`, `revision_number`, `source_scope`, `output_goal`, and `precedence`.

- [ ] **Step 6: Implement dry-run load and metadata**

Extend `run_dry_run` signature:

```python
def run_dry_run(..., query: str | None, from_brief: Path | None = None, allow_draft_brief: bool = False, ...)
```

Behavior:

- if `from_brief` is provided, load it with `load_research_brief(..., allow_draft=allow_draft_brief)`;
- derive `query` from `payload["task"]`;
- build query plan from the structured brief;
- include `research_brief` metadata in `signature_inputs`;
- write `research_brief` metadata into `run-state.json`, `search-record.json`, and `report.json` discovery context;
- do not write to the brief file.

- [ ] **Step 7: Implement CLI wiring and concise output reminder**

Pass `from_brief` and `allow_draft_brief` from CLI to orchestrator. In JSON output, include:

```json
"research_brief": {
  "brief_slug": "...",
  "status": "...",
  "hash": "...",
  "path": "..."
}
```

In text output, print:

```text
research_brief=<slug> status=<status> overrides_profile=true
```

- [ ] **Step 8: Run focused and adjacent tests**

Run:

```powershell
python -m pytest tests\paper_source\test_dry_run_from_brief.py tests\paper_source\test_paper_discovery_query_planner.py tests\paper_source\test_orchestrator_dry_run.py tests\paper_source\test_cli_parser.py -q
```

Expected: all pass.

- [ ] **Step 9: Commit**

Run:

```powershell
git add plugins\paper-source\scripts\build\paper_source\cli_parser.py plugins\paper-source\scripts\build\paper_source\cli.py plugins\paper-source\scripts\build\paper_source\orchestrator.py plugins\paper-source\scripts\build\paper_source\query_planner.py plugins\paper-source\scripts\build\paper_source\report_run.py tests\paper_source\test_dry_run_from_brief.py tests\paper_source\test_paper_discovery_query_planner.py tests\paper_source\test_orchestrator_dry_run.py tests\paper_source\test_cli_parser.py
git commit -m "feat: run discovery from research briefs"
```

## Task 4: Research Grill Skill Contract

**Files:**
- Create: `plugins/paper-source/skills/research-grill-me/SKILL.md`
- Create: `plugins/paper-source/skills/research-grill-me/references/research-brief-contract.md`
- Create: `plugins/paper-source/skills/research-grill-me/agents/openai.yaml`
- Modify: `plugins/paper-source/skills/routing.yaml`
- Create: `tests/paper_source/test_research_grill_skill_contract.py`
- Modify: `plugins/paper-source/tests/test_skill_bundle_contract.py`
- Modify: `tests/paper_source/test_config_onboarding_docs.py`

- [ ] **Step 1: Write failing skill contract tests**

Add:

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "plugins" / "paper-source" / "skills" / "research-grill-me" / "SKILL.md"
ROUTING = ROOT / "plugins" / "paper-source" / "skills" / "routing.yaml"
CONTRACT = ROOT / "plugins" / "paper-source" / "skills" / "research-grill-me" / "references" / "research-brief-contract.md"


def test_research_grill_skill_documents_one_question_contract():
    text = SKILL.read_text(encoding="utf-8")
    assert "one decision point per turn" in text
    assert "recommended answer" in text
    assert "explicit user confirmation" in text
    assert "research-brief create" in text


def test_research_grill_forbids_direct_paper_wiki_formal_writes():
    combined = SKILL.read_text(encoding="utf-8") + "\n" + CONTRACT.read_text(encoding="utf-8")
    assert "must not write Paper Wiki formal pages directly" in combined
    assert "wiki-ingest-brief" in combined
    assert "paper-search-mcp" in combined
    assert "academic_search" not in combined


def test_research_grill_is_primary_route():
    routing = ROUTING.read_text(encoding="utf-8")
    assert "research_grill_me:" in routing
    assert "category: primary" in routing
    assert "research-grill-me/SKILL.md" in routing
    assert "研究简报" in routing
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
python -m pytest tests\paper_source\test_research_grill_skill_contract.py plugins\paper-source\tests\test_skill_bundle_contract.py -q
```

Expected: missing skill folder/route.

- [ ] **Step 3: Add skill docs and metadata**

`SKILL.md` must be concise and include:

- read existing Paper Source config/profile before asking if discoverable;
- ask one decision point per turn;
- give a recommended answer;
- explain why the decision affects Paper Source;
- generate Chinese `research-brief.md` for the user and English `agent-brief.md` for agents;
- require explicit confirmation before confirmed brief creation;
- use `research-brief create --answers-json ... --vault ...`;
- route later discovery through `dry-run --from-brief`;
- must not write Paper Wiki formal pages directly.

`references/research-brief-contract.md` must include schema/status/source-scope/review-policy/output-goal/precedence/Paper Wiki boundary.

`agents/openai.yaml` must include `display_name`, a 25-64 character `short_description`, and a default prompt containing `$research-grill-me`.

- [ ] **Step 4: Add routing entry**

Add route:

```yaml
  research_grill_me:
    category: primary
    triggers:
      - clarify a research direction
      - grill my research idea
      - build a Research Brief
      - 研究简报
      - 帮我梳理科研方向
      - 强追问科研问题
      - 准备正式 Paper Source 检索
    skill: research-grill-me/SKILL.md
    notes:
      - one decision point per turn with a recommended answer
      - Research Briefs override Research Profile for the current task
      - Research Briefs cannot bypass source-staging or Paper Wiki handoff gates
```

- [ ] **Step 5: Run skill bundle tests and commit**

Run:

```powershell
python -m pytest tests\paper_source\test_research_grill_skill_contract.py plugins\paper-source\tests\test_skill_bundle_contract.py tests\paper_source\test_config_onboarding_docs.py -q
git add plugins\paper-source\skills\research-grill-me plugins\paper-source\skills\routing.yaml tests\paper_source\test_research_grill_skill_contract.py plugins\paper-source\tests\test_skill_bundle_contract.py tests\paper_source\test_config_onboarding_docs.py
git commit -m "feat: add research grill skill"
```

## Task 5: End-to-End Verification And Polish

**Files:**
- Modify as needed: docs/tests touched by earlier tasks only.

- [ ] **Step 1: Run focused verification**

Run:

```powershell
python -m pytest tests\paper_source\test_research_brief.py tests\paper_source\test_research_brief_cli.py tests\paper_source\test_dry_run_from_brief.py tests\paper_source\test_research_grill_skill_contract.py -q
```

Expected: all pass.

- [ ] **Step 2: Run adjacent verification**

Run:

```powershell
python -m pytest tests\paper_source\test_cli_parser.py tests\paper_source\test_paper_discovery_query_planner.py tests\paper_source\test_orchestrator_dry_run.py tests\paper_source\test_config_onboarding_docs.py plugins\paper-source\tests\test_skill_bundle_contract.py -q
```

Expected: all pass.

- [ ] **Step 3: Run full Paper Source plugin tests**

Run:

```powershell
python -m pytest tests\paper_source plugins\paper-source\tests -q
```

Expected: all pass or pre-existing unrelated failures are documented with exact failing tests.

- [ ] **Step 4: Run static diff checks**

Run:

```powershell
git diff --check
python scripts\validate_plugin.py plugins\paper-source
```

Expected: no whitespace errors and plugin validation passes.

- [ ] **Step 5: Final review and commit if needed**

If verification fixes were needed:

```powershell
git add <changed-files>
git commit -m "test: verify research brief intake"
```

Then run:

```powershell
git status --short --branch
git log --oneline --decorate -5
```

Expected: branch `research-brief-intake` contains the plan commit plus task commits and has a clean worktree.

## Plan Self-Review

- Spec coverage: tasks cover artifact layout, schema, statuses, CLI, dry-run brief ingestion, planner mapping, run metadata, review-session signature, routing, skill docs, and Paper Wiki boundary.
- Placeholder scan: no `TBD`, `TODO`, or unspecified "appropriate tests" remain; every task has exact files, commands, and expected outcomes.
- Type consistency: the plan consistently uses `research_brief_action`, `from_brief`, `allow_draft_brief`, `build_query_plan_from_research_brief`, and `paper-source-research-brief-v1`.
