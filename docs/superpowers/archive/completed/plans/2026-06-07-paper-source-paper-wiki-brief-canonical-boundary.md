# Paper Source/Paper Wiki Brief-Canonical Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `wiki-ingest-brief.json` the canonical Paper Source-to-Paper Wiki handoff, downgrade `wiki_deposition_task.json` to legacy compatibility, and keep Paper Wiki formal-page writing rules unchanged.

**Architecture:** Paper Source remains the source-bundle, approval, gate, trigger, and record layer. Paper Wiki remains the single user-facing formal paper wiki writing and maintenance layer. The implementation changes machine contracts and handoff intake first, then updates Paper Wiki/Paper Source docs and plugin metadata to match.

**Tech Stack:** Python 3, pytest, Codex plugin metadata JSON, Markdown skill/workflow docs, PowerShell verification commands.

---

## Current Evidence

- Approved spec: `docs/superpowers/specs/2026-06-07-paper-source-paper-wiki-brief-canonical-boundary-design.md`.
- Current `plugins/paper-source/scripts/build/paper_source/wiki_contracts.py` still lists external wiki skills in `REQUIRED_WIKI_SKILLS`.
- Current `plugins/paper-source/scripts/build/paper_source/stage_wiki.py` always writes `_paper_source/staging/papers/<slug>/wiki_deposition_task.json` and includes it in `promotion-plan.json` agent handoff paths.
- Current `plugins/paper-wiki/skills/paper-research-wiki/workflows/extract-papers.md` locates `wiki_deposition_task.json` during preflight.
- Current `plugins/paper-wiki/docs/paper-source-integration.md` says required inputs include both `wiki_deposition_task.json` and `wiki-ingest-brief.json`.
- Current tests encode the old broad required stack and old task-required behavior.

## File Structure

Implementation will modify existing files only:

- `plugins/paper-source/scripts/build/paper_source/wiki_contracts.py`: required/optional skill constants and validation mirror comment.
- `plugins/paper-source/scripts/build/paper_source/stage_wiki.py`: brief-first staging, optional legacy task generation, batch handoff metadata.
- `plugins/paper-source/scripts/build/paper_source/paper_gate.py`: brief-first ready check wording and required rule-source expectations.
- `plugins/paper-source/scripts/build/paper_source/wiki_ingest_handoff.py`: handoff checklist and rendered text.
- `plugins/paper-source/scripts/build/paper_source/wiki_ingest_trigger.py`: Paper Wiki-first trigger instruction.
- `plugins/paper-source/scripts/build/paper_source/wiki_ingest_record.py`: final-source-review skill usage validation and optional legacy sidecar recording.
- `tests/paper_source/test_wiki_deposition_task.py`: rename and update to brief-canonical staging tests plus explicit legacy generation test.
- `tests/paper_source/test_wiki_ingest_handoff.py`: new required skill stack, optional helper/reference expectations, Paper Wiki trigger text.
- `tests/paper_source/test_wiki_ingest_record.py`: final review accepts new required stack and records optional legacy task when present.
- `tests/paper_source/test_paper_gate.py`: missing brief fails; missing task does not fail.
- `tests/paper_source/test_one_paper_ingest.py`: default ingest produces canonical brief and does not depend on task.
- `tests/paper_research_wiki/test_plugin_contract.py`: Paper Wiki brief-first intake contract and unchanged formal-page quality checks.
- `plugins/paper-wiki/skills/paper-research-wiki/references/paper-source-artifact-contract.md`: brief canonical, task legacy.
- `plugins/paper-wiki/skills/paper-research-wiki/workflows/extract-papers.md`: locate `wiki-ingest-brief.json` first.
- `plugins/paper-wiki/skills/paper-research-wiki/workflows/check-wiki.md`: pending handoffs use brief-first readiness.
- `plugins/paper-wiki/docs/paper-source-integration.md`: Paper Source/Paper Wiki boundary contract.
- `plugins/paper-wiki/skills/paper-research-wiki/SKILL.md`: always-apply wording for brief canonical and legacy task.
- `plugins/paper-source/skills/paper-source-paper-deposition/SKILL.md`: thin legacy compatibility adapter.
- `plugins/paper-source/skills/paper-source-paper-deposition/workflows/formal-wiki-write.md`: thin workflow that requires brief-first recovery before Paper Wiki writing.
- `plugins/paper-source/skills/paper-ingest/SKILL.md`: brief-first formal deposition wording.
- `plugins/paper-source/skills/paper-ingest/workflows/approval-and-trigger.md`: Paper Wiki trigger wording.
- `plugins/paper-source/docs/paper-source-linkage.md`, `plugins/paper-source/docs/workflow.md`, `plugins/paper-source/docs/structure.md`, `plugins/paper-source/docs/progress.md`: detailed but single-model boundary docs.
- `plugins/paper-source/.codex-plugin/plugin.json`, `plugins/paper-wiki/.codex-plugin/plugin.json`: bump patch version and short descriptions.

Do not edit the existing formal-page writing rules except to preserve their references:

- `plugins/paper-wiki/rules/wiki-writing-standard.md`
- `plugins/paper-wiki/rules/formal-page-frontmatter.md`
- `plugins/paper-wiki/skills/paper-wiki-language/**`
- existing formal pages in `D:\paper-research-wiki`

## Implementation Tasks

### Task 1: Paper Source Required Skill Contract

**Files:**
- Modify: `tests/paper_source/test_wiki_deposition_task.py`
- Modify: `tests/paper_source/test_wiki_ingest_handoff.py`
- Modify: `tests/paper_source/test_wiki_ingest_record.py`
- Modify: `tests/paper_source/test_one_paper_ingest.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/wiki_contracts.py`

- [ ] **Step 1: Update test expected skill constants**

In each listed test file, replace the old broad expected list with:

```python
EXPECTED_RESEARCH_WIKI_SKILLS = [
    "paper-research-wiki",
    "paper-source-paper-deposition",
]
```

In `tests/paper_source/test_wiki_deposition_task.py`, replace `EXPECTED_CORE_SKILLS` with the same two-item list:

```python
EXPECTED_CORE_SKILLS = [
    "paper-research-wiki",
    "paper-source-paper-deposition",
]
```

- [ ] **Step 2: Run focused tests and confirm failure**

Run:

```powershell
python -m pytest tests/paper_source/test_wiki_deposition_task.py tests/paper_source/test_wiki_ingest_handoff.py tests/paper_source/test_wiki_ingest_record.py tests/paper_source/test_one_paper_ingest.py -q
```

Expected: failures showing generated `required_wiki_skills`, `wiki_skill_used`, or `required_skills` still include `llm-wiki`, `wiki-ingest`, `wiki-context-pack`, `wiki-lint`, `wiki-stage-commit`, `wiki-status`, `wiki-query`, `wiki-provenance`, and `tag-taxonomy`.

- [ ] **Step 3: Update `wiki_contracts.py` constants**

Change:

```python
REQUIRED_WIKI_SKILLS: tuple[str, ...] = (
    PAPER_WIKI_CANONICAL_SKILL,
    PAPER_SOURCE_DEPOSITION_SKILL,
    "llm-wiki",
    "wiki-ingest",
    "wiki-context-pack",
    "wiki-lint",
    "wiki-stage-commit",
    "wiki-status",
    "wiki-query",
    "wiki-provenance",
    "tag-taxonomy",
)
```

to:

```python
REQUIRED_WIKI_SKILLS: tuple[str, ...] = (
    PAPER_WIKI_CANONICAL_SKILL,
    PAPER_SOURCE_DEPOSITION_SKILL,
)
```

Change optional/helper grouping to:

```python
OPTIONAL_WIKI_SKILLS: tuple[str, ...] = (
    "llm-wiki",
    "wiki-ingest",
    "wiki-context-pack",
    "wiki-status",
    "wiki-query",
    "wiki-dashboard",
    "wiki-digest",
    "wiki-export",
)

QUALITY_ENHANCEMENT_WIKI_SKILLS: tuple[str, ...] = (
    "wiki-lint",
    "wiki-stage-commit",
    "wiki-provenance",
    "tag-taxonomy",
    "wiki-synthesize",
    "wiki-dedup",
    "cross-linker",
)
```

Add this comment immediately before `FORMAL_PAGE_FAMILIES`:

```python
# Paper Wiki rules are the human-readable canonical page-writing contract.
# These constants are Paper Source-side validation mirrors for generated handoffs and records.
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m pytest tests/paper_source/test_wiki_deposition_task.py tests/paper_source/test_wiki_ingest_handoff.py tests/paper_source/test_wiki_ingest_record.py tests/paper_source/test_one_paper_ingest.py -q
```

Expected: remaining failures are about `wiki_deposition_task.json` still being generated/required and local helper source wording, not broad required skills.

- [ ] **Step 5: Commit Task 1**

Run:

```powershell
git add tests/paper_source/test_wiki_deposition_task.py tests/paper_source/test_wiki_ingest_handoff.py tests/paper_source/test_wiki_ingest_record.py tests/paper_source/test_one_paper_ingest.py plugins/paper-source/scripts/build/paper_source/wiki_contracts.py
git commit -m "feat: shrink Paper Source required wiki skill contract"
```

### Task 2: Default Staging Emits Brief, Not Legacy Task

**Files:**
- Modify: `tests/paper_source/test_wiki_deposition_task.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/stage_wiki.py`

- [ ] **Step 1: Rename and rewrite default staging test**

In `tests/paper_source/test_wiki_deposition_task.py`, rename `test_stage_paper_writes_stable_wiki_deposition_task_contract` to:

```python
def test_stage_paper_writes_brief_canonical_handoff_by_default(tmp_path):
```

Replace the first task assertions with:

```python
staging_root = stage_paper(vault, slug, paper_root)

brief_path = staging_root / "wiki-ingest-brief.json"
task_path = staging_root / "wiki_deposition_task.json"
plan_path = staging_root / "promotion-plan.json"

assert brief_path.is_file()
assert not task_path.exists()

brief = json.loads(brief_path.read_text(encoding="utf-8"))
plan = json.loads(plan_path.read_text(encoding="utf-8"))

assert brief["schema_version"] == "paper-source-wiki-ingest-brief-v1"
assert brief["handoff_type"] == "agent-mediated-wiki-ingest"
assert brief["ingest_policy"]["required_wiki_skills"] == EXPECTED_CORE_SKILLS
assert brief["wiki_skill_handoff"]["required_skills"] == EXPECTED_CORE_SKILLS
assert brief["legacy_wiki_deposition_task"]["status"] == "not-emitted"
assert brief["legacy_wiki_deposition_task"]["reason"] == "wiki-ingest-brief.json is the canonical Paper Source-to-Paper Wiki handoff"
assert plan["wiki_ingest_brief_path"] == str(brief_path)
assert "wiki_deposition_task_path" not in plan
assert str(task_path) not in plan["agent_handoff_paths"]
```

Keep page-family, frontmatter, quality gate, agent-context, and Paper Wiki-before-local-source checks against `brief`, not `task`.

- [ ] **Step 2: Add explicit legacy-generation test**

Add a second test:

```python
def test_stage_paper_can_emit_legacy_wiki_deposition_task_when_requested(tmp_path):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    paper_root = _seed_source_bundle(vault, slug)

    staging_root = stage_paper(vault, slug, paper_root, emit_legacy_deposition_task=True)

    task_path = staging_root / "wiki_deposition_task.json"
    assert task_path.is_file()
    task = json.loads(task_path.read_text(encoding="utf-8"))
    brief = json.loads((staging_root / "wiki-ingest-brief.json").read_text(encoding="utf-8"))
    plan = json.loads((staging_root / "promotion-plan.json").read_text(encoding="utf-8"))

    assert task["schema_version"] == "paper-source-wiki-deposition-task-v1"
    assert task["required_skills"] == EXPECTED_CORE_SKILLS
    assert brief["legacy_wiki_deposition_task"]["status"] == "emitted"
    assert brief["legacy_wiki_deposition_task"]["task_path"] == str(task_path)
    assert plan["legacy_wiki_deposition_task_path"] == str(task_path)
    assert str(task_path) in plan["agent_handoff_paths"]
```

- [ ] **Step 3: Run tests and confirm signature failure**

Run:

```powershell
python -m pytest tests/paper_source/test_wiki_deposition_task.py -q
```

Expected: failure with `TypeError: stage_paper() got an unexpected keyword argument 'emit_legacy_deposition_task'`, plus default test failure because task is still generated.

- [ ] **Step 4: Update `stage_paper` signature**

In `plugins/paper-source/scripts/build/paper_source/stage_wiki.py`, change:

```python
def stage_paper(vault_path: Path, slug: str, paper_root: Path, workflow_mode: str = FAST_INGEST_MODE) -> Path:
```

to:

```python
def stage_paper(
    vault_path: Path,
    slug: str,
    paper_root: Path,
    workflow_mode: str = FAST_INGEST_MODE,
    *,
    emit_legacy_deposition_task: bool = False,
) -> Path:
```

- [ ] **Step 5: Make legacy task conditional**

Replace the unconditional task build/write block:

```python
wiki_deposition_task = _build_wiki_deposition_task(...)
...
write_json_atomic(wiki_deposition_task_path, wiki_deposition_task)
```

with:

```python
wiki_deposition_task = None
if emit_legacy_deposition_task:
    wiki_deposition_task = _build_wiki_deposition_task(
        vault_path=vault_path,
        slug=slug,
        title=title,
        workflow_mode=workflow_mode,
        paper_root=paper_root,
        staging_root=staging_root,
        wiki_ingest_brief_path=wiki_ingest_brief_path,
        reading_report_path=reading_report_path,
        source_reader_path=source_reader_path,
        reader_artifacts=reader_artifacts,
        critic_artifacts=critic_artifacts,
        wiki_ingest_brief=wiki_ingest_brief,
    )
    write_json_atomic(wiki_deposition_task_path, wiki_deposition_task)
```

- [ ] **Step 6: Update brief legacy task payload**

In `_build_wiki_ingest_brief`, replace the current `wiki_deposition_task` field with:

```python
"legacy_wiki_deposition_task": {
    "schema_version": "paper-source-wiki-deposition-task-v1",
    "status": "emitted" if wiki_deposition_task_path else "not-emitted",
    "task_path": str(wiki_deposition_task_path) if wiki_deposition_task_path else None,
    "canonical_handoff": "wiki-ingest-brief.json",
    "reason": "wiki-ingest-brief.json is the canonical Paper Source-to-Paper Wiki handoff",
    "compatibility_aliases": deposition_skill_compatibility_aliases(),
},
```

Remove or stop emitting the old top-level `"wiki_deposition_task": {...}` block in new brief output.

- [ ] **Step 7: Pass `wiki_deposition_task_path` only when emitting legacy**

Where `_build_wiki_ingest_brief` is called, change:

```python
wiki_deposition_task_path=str(wiki_deposition_task_path),
```

to:

```python
wiki_deposition_task_path=str(wiki_deposition_task_path) if emit_legacy_deposition_task else None,
```

- [ ] **Step 8: Update batch handoff writer**

Change `_write_batch_handoff` signature:

```python
wiki_deposition_task_path: Path,
```

to:

```python
wiki_deposition_task_path: Path | None,
```

Change the appended paper record:

```python
"wiki_deposition_task": str(wiki_deposition_task_path),
```

to:

```python
"legacy_wiki_deposition_task": str(wiki_deposition_task_path) if wiki_deposition_task_path else None,
```

- [ ] **Step 9: Update promotion plan**

Build `agent_handoff_paths` as:

```python
agent_handoff_paths = [
    str(wiki_ingest_brief_path),
    str(batch_handoff_path),
    str(reading_report_path),
    str(source_reader_path),
]
if emit_legacy_deposition_task:
    agent_handoff_paths.insert(1, str(wiki_deposition_task_path))
```

Remove the default `"wiki_deposition_task_path": str(wiki_deposition_task_path)` field. Add this only when legacy is emitted:

```python
if emit_legacy_deposition_task:
    plan["legacy_wiki_deposition_task_path"] = str(wiki_deposition_task_path)
```

- [ ] **Step 10: Run staging tests**

Run:

```powershell
python -m pytest tests/paper_source/test_wiki_deposition_task.py tests/paper_source/test_one_paper_ingest.py -q
```

Expected: PASS or only failures in tests that still assert old `wiki_deposition_task` key names.

- [ ] **Step 11: Commit Task 2**

Run:

```powershell
git add tests/paper_source/test_wiki_deposition_task.py tests/paper_source/test_one_paper_ingest.py plugins/paper-source/scripts/build/paper_source/stage_wiki.py
git commit -m "feat: make wiki ingest brief the default staging handoff"
```

### Task 3: Gate, Handoff, Trigger, And Record Use Brief-First Boundary

**Files:**
- Modify: `tests/paper_source/test_paper_gate.py`
- Modify: `tests/paper_source/test_wiki_ingest_handoff.py`
- Modify: `tests/paper_source/test_wiki_ingest_record.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/paper_gate.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/wiki_ingest_handoff.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/wiki_ingest_trigger.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/wiki_ingest_record.py`

- [ ] **Step 1: Add paper-gate no-task ready test**

In `tests/paper_source/test_paper_gate.py`, add this test using the existing `_seed_paper_gate_fixture` helper:

```python
def test_paper_gate_accepts_complete_brief_without_legacy_deposition_task(tmp_path):
    vault = tmp_path / "vault"
    slug = "fixture-paper"
    _seed_paper_gate_fixture(vault, slug, staged=True)
    task_path = vault / "_paper_source" / "staging" / "papers" / slug / "wiki_deposition_task.json"
    if task_path.exists():
        task_path.unlink()

    gate = build_paper_gate(vault, slug)

    assert gate["status"] in {"waiting_for_human_gate", "ready_for_wiki_ingest_agent"}
    check_runs = {run["name"]: run["conclusion"] for run in gate["check_suite"]["check_runs"]}
    assert check_runs["wiki-ingest-brief"] == "success"
    assert "wiki-deposition-task" not in check_runs
```

- [ ] **Step 2: Update handoff/trigger expected text**

In `tests/paper_source/test_wiki_ingest_handoff.py`, update trigger assertions to require Paper Wiki-first wording:

```python
assert "paper-research-wiki" in trigger["instruction"]
assert "wiki-ingest-brief.json" in trigger["instruction"]
assert "Load llm-wiki" not in trigger["instruction"]
assert "tag-taxonomy" not in trigger["required_wiki_skills"]
```

Keep provenance policy assertions, but point them at policy text, not required skill list:

```python
assert "source-first" in trigger["instruction"]
assert "Preserve support status" in trigger["instruction"]
```

- [ ] **Step 3: Update final review skill usage tests**

In `tests/paper_source/test_wiki_ingest_record.py`, update seeded final-source-review payloads so:

```python
"wiki_batch_ingest": {
    "status": "completed",
    "wiki_skill_used": ["paper-research-wiki", "paper-source-paper-deposition"],
    "optional_helpers_used": ["wiki-provenance", "tag-taxonomy"],
    "paper_slugs": [slug],
}
```

Add assertion after record creation:

```python
assert record["final_source_review"]["wiki_batch_ingest"]["wiki_skill_used"] == EXPECTED_RESEARCH_WIKI_SKILLS
assert record["final_source_review"]["wiki_batch_ingest"].get("optional_helpers_used") == ["wiki-provenance", "tag-taxonomy"]
```

- [ ] **Step 4: Run focused tests and confirm failures**

Run:

```powershell
python -m pytest tests/paper_source/test_paper_gate.py tests/paper_source/test_wiki_ingest_handoff.py tests/paper_source/test_wiki_ingest_record.py -q
```

Expected: failures in trigger instruction wording and paper-gate rule-source expectations, if implementation still requires local broad stack wording.

- [ ] **Step 5: Update `paper_gate.py` rule-source expectations**

In `plugins/paper-source/scripts/build/paper_source/paper_gate.py`, change:

```python
required_rule_sources = [
    "target vault AGENTS.md",
    "_meta/schema.md",
    "Ar9av/obsidian-wiki",
    "kepano/obsidian-skills",
    "initiatione/obsidian-wiki-dev",
    "local llm-wiki / wiki-ingest / obsidian-markdown skills",
]
```

to:

```python
required_rule_sources = [
    "target vault AGENTS.md",
    "_meta/schema.md",
    "paper-research-wiki",
    "Ar9av/obsidian-wiki",
    "kepano/obsidian-skills",
    "initiatione/obsidian-wiki-dev",
]
```

Keep the helper/adapter check, but allow helper wording to appear in roles rather than requiring the old local source item:

```python
if "helper" not in resolution_source_text.lower() and "helper" not in write_requirement_text.lower():
    issues.append("external wiki skills must be described as optional helpers or references")
```

- [ ] **Step 6: Update `wiki_ingest_handoff.py` checklist**

Replace the checklist item:

```python
"Load the wiki-ingest skill before writing final pages; use Paper Source artifacts only as source/evidence inputs.",
```

with:

```python
"Invoke Paper Wiki $paper-research-wiki for formal wiki writing; use wiki-ingest-brief.json as the canonical source/evidence handoff.",
```

Add a checklist item immediately after it:

```python
"External wiki skills such as llm-wiki, wiki-ingest, wiki-provenance, tag-taxonomy, and wiki-lint are optional helpers or internalized Paper Wiki policies, not required runtime dependencies.",
```

- [ ] **Step 7: Update `wiki_ingest_trigger.py` ready instruction**

Replace the beginning of `_ready_instruction`:

```python
"Continue as the current wiki ingest agent. Load "
+ ", ".join(required_skills)
+ " before writing formal pages; use wiki-provenance for claim support and tag-taxonomy for final tags. "
```

with:

```python
"Continue by invoking Paper Wiki $paper-research-wiki for formal paper wiki writing. "
"Use wiki-ingest-brief.json as the canonical Paper Source source/evidence handoff; "
"keep paper-source-paper-deposition only as a legacy compatibility adapter. "
"Apply Paper Wiki provenance, tag, language, lint, and post-task-check policies through the Paper Wiki writing standard. "
```

Ensure `_ready_instruction` includes `wiki-ingest-brief.json` literally.

- [ ] **Step 8: Update `wiki_ingest_record.py` validation wording**

In `_validate_wiki_batch_ingest_section`, keep requiring only `required_wiki_skills()`. Do not require optional helper names. Add optional helper preservation by not rejecting `optional_helpers_used`:

```python
optional_helpers = section.get("optional_helpers_used") or []
if optional_helpers and not isinstance(optional_helpers, list):
    failures.append("final source review wiki_batch_ingest optional_helpers_used must be a list")
```

- [ ] **Step 9: Run focused tests**

Run:

```powershell
python -m pytest tests/paper_source/test_paper_gate.py tests/paper_source/test_wiki_ingest_handoff.py tests/paper_source/test_wiki_ingest_record.py -q
```

Expected: PASS.

- [ ] **Step 10: Commit Task 3**

Run:

```powershell
git add tests/paper_source/test_paper_gate.py tests/paper_source/test_wiki_ingest_handoff.py tests/paper_source/test_wiki_ingest_record.py plugins/paper-source/scripts/build/paper_source/paper_gate.py plugins/paper-source/scripts/build/paper_source/wiki_ingest_handoff.py plugins/paper-source/scripts/build/paper_source/wiki_ingest_trigger.py plugins/paper-source/scripts/build/paper_source/wiki_ingest_record.py
git commit -m "feat: route Paper Source handoffs through Paper Wiki brief-first boundary"
```

### Task 4: Paper Wiki Intake Docs And Contract Tests

**Files:**
- Modify: `tests/paper_research_wiki/test_plugin_contract.py`
- Modify: `plugins/paper-wiki/skills/paper-research-wiki/references/paper-source-artifact-contract.md`
- Modify: `plugins/paper-wiki/skills/paper-research-wiki/workflows/extract-papers.md`
- Modify: `plugins/paper-wiki/skills/paper-research-wiki/workflows/check-wiki.md`
- Modify: `plugins/paper-wiki/docs/paper-source-integration.md`
- Modify: `plugins/paper-wiki/skills/paper-research-wiki/SKILL.md`

- [ ] **Step 1: Update Paper Wiki contract tests for brief-first language**

In `tests/paper_research_wiki/test_plugin_contract.py`, update `test_public_skill_defaults_paper_source_wiki_requests_to_deposition` so it requires both:

```python
assert "wiki-ingest-brief.json" in skill
assert "legacy `wiki_deposition_task.json`" in skill
```

Update `test_paper_source_integration_docs_name_handoff_and_record_contracts` to assert:

```python
assert "canonical handoff" in text
assert "legacy compatibility" in text
assert "wiki-ingest-brief.json" in text
assert "wiki_deposition_task.json" in text
```

Add a new test:

```python
def test_paper_wiki_paper_source_artifact_contract_is_brief_first():
    contract = _read(PUBLIC_SKILL / "references" / "paper-source-artifact-contract.md")
    extract = _read(PUBLIC_SKILL / "workflows" / "extract-papers.md")
    check = _read(PUBLIC_SKILL / "workflows" / "check-wiki.md")
    integration = _read(PLUGIN / "docs" / "paper-source-integration.md")
    combined = "\n".join([contract, extract, check, integration])

    assert "canonical handoff" in contract
    assert "wiki-ingest-brief.json" in contract
    assert "wiki_deposition_task.json" in contract
    assert "legacy compatibility" in contract
    assert "Locate `_paper_source/staging/papers/*/wiki-ingest-brief.json`" in extract
    assert "Do not treat task-only legacy handoffs as ready" in combined
```

- [ ] **Step 2: Run Paper Wiki tests and confirm failure**

Run:

```powershell
python -m pytest tests/paper_research_wiki/test_plugin_contract.py -q
```

Expected: failures because Paper Wiki docs still say both artifacts are required and extract preflight locates task files first.

- [ ] **Step 3: Update `paper-source-artifact-contract.md`**

Replace current content with:

```markdown
# Paper Source Artifact Contract

Canonical handoff:

- `wiki-ingest-brief.json`

Legacy compatibility artifact:

- `wiki_deposition_task.json`

Required source inputs for Paper Wiki deposition:

- `briefs/reading-report.md`
- `metadata.json`
- `paper.pdf`
- MinerU Markdown, TeX, images, and manifest

Optional aids are reader evidence maps, claim support JSON, critic reports, and `wiki-agent-trigger.json`.

Paper Wiki must not treat task-only legacy handoffs as ready. If `wiki_deposition_task.json` exists without `wiki-ingest-brief.json`, report the legacy limitation and route back to Paper Source to regenerate or repair the brief before formal writes.

Paper Source owns `paper-gate`, human approval records, and `record-wiki-ingest`.
```

- [ ] **Step 4: Update `extract-papers.md` preflight**

Change step 4 from locating task files to:

```markdown
4. Locate `_paper_source/staging/papers/*/wiki-ingest-brief.json`; this is the canonical Paper Source-to-Paper Wiki handoff.
5. Treat `_paper_source/staging/papers/*/wiki_deposition_task.json` as legacy compatibility only. Do not treat task-only legacy handoffs as ready; route them back to Paper Source to regenerate or repair `wiki-ingest-brief.json`.
6. Run a readiness preflight and group papers as ready, needs human approval, blocked, already recorded, or legacy-needs-brief-repair.
7. For ready papers, read source bundle artifacts before writing: PDF, metadata, MinerU Markdown, TeX, images, manifest, reading report, and `wiki-ingest-brief.json`.
```

- [ ] **Step 5: Update `check-wiki.md` pending handoff language**

Add under `Check:`:

```markdown
- pending Paper Source handoffs, using `_paper_source/staging/papers/*/wiki-ingest-brief.json` as canonical and treating task-only `wiki_deposition_task.json` folders as legacy-needs-brief-repair
```

Replace the older generic `pending Paper Source handoffs` bullet with this more specific bullet.

- [ ] **Step 6: Update `paper-source-integration.md`**

Change the required input sentence to:

```markdown
The canonical Paper Source-to-Paper Wiki handoff is `wiki-ingest-brief.json`. Required inputs include the brief, reading report, metadata, PDF, MinerU Markdown, TeX, images, and manifest. `wiki_deposition_task.json` is a legacy compatibility artifact; Paper Wiki may read it for historical context, but task-only legacy handoffs are not ready for formal writes until Paper Source regenerates or repairs the brief.
```

- [ ] **Step 7: Update Paper Wiki `SKILL.md`**

Replace the always-apply bullet:

```markdown
- `wiki_deposition_task.json` and `wiki-ingest-brief.json` are the normal Paper Source handoff artifacts for deposition; resolve the target vault `AGENTS.md` and `_meta/*` contract before formal writes.
```

with:

```markdown
- `wiki-ingest-brief.json` is the canonical Paper Source handoff artifact for deposition; `wiki_deposition_task.json` is legacy compatibility only. Task-only legacy handoffs need Paper Source brief repair before formal writes.
```

- [ ] **Step 8: Run Paper Wiki tests**

Run:

```powershell
python -m pytest tests/paper_research_wiki/test_plugin_contract.py -q
```

Expected: PASS.

- [ ] **Step 9: Commit Task 4**

Run:

```powershell
git add tests/paper_research_wiki/test_plugin_contract.py plugins/paper-wiki/skills/paper-research-wiki/references/paper-source-artifact-contract.md plugins/paper-wiki/skills/paper-research-wiki/workflows/extract-papers.md plugins/paper-wiki/skills/paper-research-wiki/workflows/check-wiki.md plugins/paper-wiki/docs/paper-source-integration.md plugins/paper-wiki/skills/paper-research-wiki/SKILL.md
git commit -m "docs: make Paper Wiki Paper Source intake brief-first"
```

### Task 5: Thin Paper Source Deposition Compatibility Adapter

**Files:**
- Modify: `tests/paper_source/test_wiki_deposition_task.py`
- Modify: `plugins/paper-source/tests/test_skill_bundle_contract.py`
- Modify: `tests/paper_research_wiki/test_plugin_contract.py`
- Modify: `plugins/paper-source/skills/paper-source-paper-deposition/SKILL.md`
- Modify: `plugins/paper-source/skills/paper-source-paper-deposition/workflows/formal-wiki-write.md`

- [ ] **Step 1: Update adapter tests to require thin alias**

In `tests/paper_source/test_wiki_deposition_task.py`, replace the broad adapter stack test loop with:

```python
assert "wiki-ingest-brief.json" in text
assert "legacy `wiki_deposition_task.json`" in text
assert "$paper-research-wiki" in text
assert "epi-wiki-deposition" in text
assert "llm-wiki" not in text
assert "wiki-stage-commit" not in text
assert "Required frontmatter fields" not in text
```

In `plugins/paper-source/tests/test_skill_bundle_contract.py`, update `test_paper_source_paper_deposition_documents_required_wiki_adapter_stack` to:

```python
def test_paper_source_paper_deposition_is_thin_legacy_adapter():
    deposition = (SKILLS / "paper-source-paper-deposition" / "SKILL.md").read_text(encoding="utf-8")
    formal_workflow = (
        SKILLS / "paper-source-paper-deposition" / "workflows" / "formal-wiki-write.md"
    ).read_text(encoding="utf-8")
    combined = "\n".join([deposition, formal_workflow])

    assert "workflows/formal-wiki-write.md" in deposition
    assert "wiki-ingest-brief.json" in combined
    assert "legacy `wiki_deposition_task.json`" in combined
    assert "epi-wiki-deposition" in deposition
    assert "$paper-research-wiki" in combined
    assert "compatibility adapter" in combined
    assert "llm-wiki" not in combined
    assert "wiki-stage-commit" not in combined
    assert "Required frontmatter fields" not in combined
    assert "must not enter the formal graph" in combined
```

- [ ] **Step 2: Run adapter tests and confirm failure**

Run:

```powershell
python -m pytest tests/paper_source/test_wiki_deposition_task.py plugins/paper-source/tests/test_skill_bundle_contract.py tests/paper_research_wiki/test_plugin_contract.py::test_paper_source_bridge_points_to_plugin_level_experience -q
```

Expected: failures because adapter docs still contain full stack and repeated frontmatter/page-family rules.

- [ ] **Step 3: Rewrite `paper-source-paper-deposition/SKILL.md` as thin adapter**

Use this body after frontmatter:

```markdown
# Paper Source Paper Deposition

Use this skill only as the legacy compatibility adapter at the Paper Source-to-Paper Wiki boundary.

Canonical path: formal paper wiki work goes through Paper Wiki `$paper-research-wiki` using `_paper_source/staging/papers/<slug>/wiki-ingest-brief.json` as the handoff.

Legacy compatibility: older artifacts may say `wiki_deposition_task.json` or `epi-wiki-deposition`. Treat those as legacy names and route the user to Paper Wiki after confirming that `wiki-ingest-brief.json` exists. If only the legacy task exists, ask Paper Source to regenerate or repair the brief before formal writes.

## Workflow Routing

| Intent | Load |
| --- | --- |
| User-facing formal paper wiki writing, extraction, checks, updates, relinking, or graph-aware rewrite | `$paper-research-wiki` from Paper Wiki |
| Legacy handoff mentions `wiki_deposition_task.json` or `epi-wiki-deposition` | `workflows/formal-wiki-write.md` |

## Boundaries

- Paper Source source bundles and `_paper_source/` artifacts are evidence inputs, not formal wiki pages.
- Paper Source owns `paper-gate`, human approval records, and `record-wiki-ingest`.
- Paper Wiki owns formal page writing, graph-aware rewrite, provenance sidecars, language gate, link repair, and post-task checks.
- Internal `_paper_source/` and legacy `_epi/` pages must not enter the formal graph.
```

- [ ] **Step 4: Rewrite `formal-wiki-write.md` as thin workflow**

Use this content:

```markdown
# Formal Wiki Write Compatibility Adapter

Use this workflow only when a legacy Paper Source deposition request names `wiki_deposition_task.json` or `epi-wiki-deposition`.

## Load Inputs

1. Locate `_paper_source/staging/papers/<slug>/wiki-ingest-brief.json`.
2. If `wiki-ingest-brief.json` is missing and only `wiki_deposition_task.json` exists, stop and route back to Paper Source to regenerate or repair the brief.
3. Read the target vault `AGENTS.md` and `_meta/*` contract files when present.

## Route

Invoke Paper Wiki `$paper-research-wiki` for formal paper wiki work. Paper Wiki owns source-first deposition, graph-aware rewrite, provenance, language, link repair, QMD boundary reporting, `final-source-review.json`, and post-task checks.

This adapter does not duplicate Paper Wiki page-family, frontmatter, language, or lint rules. It only preserves compatibility with old Paper Source artifact names.

Internal `_paper_source/` and legacy `_epi/` pages must not enter the formal graph.
```

- [ ] **Step 5: Run adapter tests**

Run:

```powershell
python -m pytest tests/paper_source/test_wiki_deposition_task.py plugins/paper-source/tests/test_skill_bundle_contract.py tests/paper_research_wiki/test_plugin_contract.py::test_paper_source_bridge_points_to_plugin_level_experience -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 5**

Run:

```powershell
git add tests/paper_source/test_wiki_deposition_task.py plugins/paper-source/tests/test_skill_bundle_contract.py tests/paper_research_wiki/test_plugin_contract.py plugins/paper-source/skills/paper-source-paper-deposition/SKILL.md plugins/paper-source/skills/paper-source-paper-deposition/workflows/formal-wiki-write.md
git commit -m "docs: thin Paper Source deposition compatibility adapter"
```

### Task 6: Paper Source Docs And Skill Docs Match Brief-First Contract

**Files:**
- Modify: `tests/paper_source/test_current_docs.py`
- Modify: `tests/paper_source/test_paper_source_linkage_doc.py`
- Modify: `plugins/paper-source/docs/paper-source-linkage.md`
- Modify: `plugins/paper-source/docs/workflow.md`
- Modify: `plugins/paper-source/docs/structure.md`
- Modify: `plugins/paper-source/docs/progress.md`
- Modify: `plugins/paper-source/skills/paper-ingest/SKILL.md`
- Modify: `plugins/paper-source/skills/paper-ingest/workflows/approval-and-trigger.md`
- Modify: `plugins/paper-source/skills/wiki-setup/SKILL.md`
- Modify: `plugins/paper-source/skills/wiki-provenance/SKILL.md`

- [ ] **Step 1: Update docs tests**

Update tests that currently require broad stack wording so they require:

```python
for phrase in [
    "wiki-ingest-brief.json",
    "canonical Paper Source-to-Paper Wiki handoff",
    "wiki_deposition_task.json is legacy",
    "paper-research-wiki",
    "paper-source-paper-deposition",
    "external wiki skills are optional helpers",
]:
    assert phrase in text
```

Keep assertions for:

```python
for phrase in [
    "Ar9av/obsidian-wiki",
    "kepano/obsidian-skills",
    "initiatione/obsidian-wiki-dev",
    "wiki_rule_source_model",
    "record-wiki-ingest",
    "final-source-review.json",
]:
    assert phrase in text
```

- [ ] **Step 2: Run docs tests and confirm failure**

Run:

```powershell
python -m pytest tests/paper_source/test_current_docs.py tests/paper_source/test_paper_source_linkage_doc.py -q
```

Expected: failures because docs still describe `wiki_deposition_task.json` as normal and broad external stack as required.

- [ ] **Step 3: Update `paper-source-linkage.md`**

Make these targeted changes:

- In the rule-source model section, state that Paper Wiki `$paper-research-wiki` is the canonical execution layer.
- State that external wiki skills are optional helpers or internalized Paper Wiki policies, not runtime required dependencies.
- Replace “`wiki-ingest-brief` 与 `wiki_deposition_task.json` 检查必须验证...” with wording that `wiki-ingest-brief.json` is canonical and `wiki_deposition_task.json` is legacy-compatible only.
- In artifact lists, mark `wiki_deposition_task.json` as `legacy optional`.
- In Step 7/8/trigger prose, say trigger routes to Paper Wiki using the brief.
- Preserve detailed source-first, QMD boundary, final-source-review, and record-wiki-ingest validation details.

- [ ] **Step 4: Update `workflow.md`**

Change the final handoff paragraph so it says:

```markdown
`wiki-ingest-brief.json` is the canonical Paper Source-to-Paper Wiki handoff. New staging does not require `wiki_deposition_task.json`; that file is legacy compatibility only. The next formal write step is Paper Wiki `$paper-research-wiki`, while Paper Source keeps ownership of `paper-gate`, human approval, `wiki-ingest-trigger`, and `record-wiki-ingest`.
```

Do not rewrite the whole workflow doc in this task.

- [ ] **Step 5: Update `structure.md` and `progress.md`**

In `structure.md`, update module/artifact descriptions for `stage_wiki.py`, `paper_gate.py`, and `wiki_ingest_record.py` to brief-first wording.

In `progress.md`, add a current status entry:

```markdown
- Paper Source/Paper Wiki boundary: `wiki-ingest-brief.json` is the canonical handoff; `wiki_deposition_task.json` is legacy compatibility only; Paper Wiki `$paper-research-wiki` is the formal paper wiki writing layer.
```

Do not move old changelog content in this task. This task only adds the current boundary status line and updates stale boundary wording.

- [ ] **Step 6: Update Paper Source skill docs**

In `paper-ingest/SKILL.md`, replace “formal wiki deposition from an Paper Source source bundle or `wiki_deposition_task.json`” with:

```markdown
For formal wiki deposition from an Paper Source source bundle, switch to Paper Wiki `$paper-research-wiki` using `wiki-ingest-brief.json`; use `paper-source-paper-deposition` only for legacy `wiki_deposition_task.json` or `epi-wiki-deposition` mentions.
```

In `approval-and-trigger.md`, replace “external wiki-ingest agent” with “Paper Wiki `$paper-research-wiki` or another wiki-capable agent following the Paper Wiki/vault contract”.

In `wiki-setup/SKILL.md`, replace required stack wording with brief-first and optional helper wording.

In `wiki-provenance/SKILL.md`, keep provenance requirements mandatory but avoid saying the standalone `wiki-provenance` skill is required runtime stack.

- [ ] **Step 7: Run docs tests**

Run:

```powershell
python -m pytest tests/paper_source/test_current_docs.py tests/paper_source/test_paper_source_linkage_doc.py plugins/paper-source/tests/test_skill_bundle_contract.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit Task 6**

Run:

```powershell
git add tests/paper_source/test_current_docs.py tests/paper_source/test_paper_source_linkage_doc.py plugins/paper-source/docs/paper-source-linkage.md plugins/paper-source/docs/workflow.md plugins/paper-source/docs/structure.md plugins/paper-source/docs/progress.md plugins/paper-source/skills/paper-ingest/SKILL.md plugins/paper-source/skills/paper-ingest/workflows/approval-and-trigger.md plugins/paper-source/skills/wiki-setup/SKILL.md plugins/paper-source/skills/wiki-provenance/SKILL.md
git commit -m "docs: align Paper Source docs with brief-first Paper Wiki boundary"
```

### Task 7: Version Bump And Plugin Metadata

**Files:**
- Modify: `plugins/paper-source/.codex-plugin/plugin.json`
- Modify: `plugins/paper-wiki/.codex-plugin/plugin.json`
- Modify: `tests/paper_research_wiki/test_plugin_contract.py`

- [ ] **Step 1: Update metadata tests**

In `tests/paper_research_wiki/test_plugin_contract.py`, update plugin version expectations from `0.2.0` to `0.2.1`.

Search for Paper Source version assertions and update exact `0.2.0` expectations to `0.2.1`:

```powershell
rg -n "\"0\\.2\\.0\"|v0\\.2\\.0" tests plugins/paper-source/tests plugins/paper-source/.codex-plugin plugins/paper-wiki/.codex-plugin
```

- [ ] **Step 2: Run metadata tests and confirm failure**

Run:

```powershell
python -m pytest tests/paper_research_wiki/test_plugin_contract.py plugins/paper-source/tests -q
```

Expected: failures on plugin version metadata until JSON files are updated.

- [ ] **Step 3: Bump Paper Source plugin metadata**

In `plugins/paper-source/.codex-plugin/plugin.json`:

```json
"version": "0.2.1"
```

Change `description` to:

```json
"description": "Discover, acquire, parse, stage, approve, hand off, query, and record academic paper knowledge for an Paper Source-compatible Paper Wiki wiki."
```

Change `interface.shortDescription` prefix to:

```json
"v0.2.1 | Find, vet, route sources, OA-acquire, brief-first hand off to Paper Wiki, wiki-ask, and record Paper Wiki requests."
```

- [ ] **Step 4: Bump Paper Wiki plugin metadata**

In `plugins/paper-wiki/.codex-plugin/plugin.json`:

```json
"version": "0.2.1"
```

Change `interface.shortDescription` prefix to:

```json
"v0.2.1 | Brief-first Paper Wiki deposition, ask, checks, update, relink, redo, record requests."
```

Keep `description` unchanged in this task because it already covers Paper Wiki's source-map-grounded wiki role.

- [ ] **Step 5: Run metadata tests**

Run:

```powershell
python -m pytest tests/paper_research_wiki/test_plugin_contract.py plugins/paper-source/tests -q
```

Expected: PASS.

- [ ] **Step 6: Commit Task 7**

Run:

```powershell
git add plugins/paper-source/.codex-plugin/plugin.json plugins/paper-wiki/.codex-plugin/plugin.json tests/paper_research_wiki/test_plugin_contract.py plugins/paper-source/tests
git commit -m "chore: bump Paper Source Paper Wiki boundary contract versions"
```

### Task 8: Full Verification

**Files:**
- No source edits unless verification exposes a bug.

- [ ] **Step 1: Run broad test suite**

Run:

```powershell
python -m pytest tests/paper_source tests/paper_research_wiki plugins/paper-source/tests -q
```

Expected: PASS.

- [ ] **Step 2: Run plugin validators**

Run with default Python first:

```powershell
python C:\Users\liuchf\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\paper-search\plugins\paper-source
python C:\Users\liuchf\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\paper-search\plugins\paper-wiki
```

Expected: PASS. If default Python fails with `ModuleNotFoundError` for validator dependencies, rerun:

```powershell
D:\MiniConda\python.exe C:\Users\liuchf\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\paper-search\plugins\paper-source
D:\MiniConda\python.exe C:\Users\liuchf\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\paper-search\plugins\paper-wiki
```

Expected: PASS.

- [ ] **Step 3: Search for stale required-stack wording**

Run:

```powershell
rg -n "required skill stack|wiki_deposition_task.json.*required|llm-wiki.*required|wiki-ingest.*required|wiki-provenance.*required|tag-taxonomy.*required" plugins tests docs
```

Expected: no hits that describe external wiki skills or `wiki_deposition_task.json` as new-flow required. Hits that describe Paper Wiki internalized policies are acceptable only if they explicitly say optional helper, internalized policy, or legacy compatibility.

- [ ] **Step 4: Search for stale generated task dependency**

Run:

```powershell
rg -n "wiki_deposition_task_path|wiki_deposition_task\"|wiki_deposition_task.json" plugins/paper-source/scripts/build/paper_source tests/paper_source tests/paper_research_wiki plugins/paper-wiki plugins/paper-source/skills plugins/paper-source/docs
```

Expected: remaining hits are in legacy compatibility docs/tests, optional sidecar recording, or explicit legacy-generation paths. No new-flow gate, handoff, trigger, or Paper Wiki preflight should require the task file.

- [ ] **Step 5: Inspect git status**

Run:

```powershell
git status --short
```

Expected: only intended files changed. Do not stage pre-existing unrelated changes such as `plugins/paper-source/docs/config.md`, `plugins/paper-source/scripts/build/paper_source/paper_search_mcp_launcher.py`, `tests/paper_source/test_current_docs.py`, or `tests/paper_source/test_runtime_config.py` unless this implementation intentionally modified them.

- [ ] **Step 6: Commit final verification fixes if needed**

If Step 1 through Step 4 exposed small fixes in files already touched by this implementation, stage only those implementation files:

```powershell
git add plugins/paper-source/scripts/build/paper_source plugins/paper-source/skills plugins/paper-source/docs plugins/paper-source/.codex-plugin/plugin.json plugins/paper-wiki/skills plugins/paper-wiki/docs plugins/paper-wiki/.codex-plugin/plugin.json tests/paper_source tests/paper_research_wiki plugins/paper-source/tests
git commit -m "test: verify Paper Source Paper Wiki brief-first boundary"
```

If no fixes were needed, run `git status --short` and report that no final verification commit was necessary.

## Completion Checklist

- [ ] `wiki-ingest-brief.json` is generated as canonical handoff for new staging.
- [ ] New default staging does not emit `wiki_deposition_task.json`.
- [ ] Explicit legacy generation can still emit valid `wiki_deposition_task.json`.
- [ ] `paper-gate` accepts complete brief without legacy task.
- [ ] `wiki-ingest-trigger` routes to Paper Wiki `$paper-research-wiki`.
- [ ] Paper Wiki docs/tests use brief-first ready checks.
- [ ] `paper-source-paper-deposition` is a thin compatibility adapter.
- [ ] External wiki skills are optional/reference/enhancement, not required runtime stack.
- [ ] Paper Wiki formal page quality rules remain unchanged.
- [ ] Paper Source and Paper Wiki versions are bumped to `0.2.1`.
- [ ] Full tests and plugin validators pass.
