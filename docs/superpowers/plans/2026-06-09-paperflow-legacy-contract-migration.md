# PaperFlow Legacy Contract Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move current PaperFlow source-visible names from legacy EPI/PRW naming to Paper Source / Paper Wiki names while preserving compatibility for existing artifacts and installed caches.

**Architecture:** New writes and source-visible folders use `paper_source`, `paper-source-*`, `_paper_source/`, and `paper-wiki-*`. Legacy `epi`, `_epi/`, `EPI_*`, `prw-*`, and `prw-record-request.json` remain readable through shims and fallback checks, but are no longer the primary names.

**Tech Stack:** Python runtime package under `plugins/paper-source/scripts/build`, Codex plugin skill bundles, pytest contract tests, PowerShell filesystem operations.

---

### Task 1: Lock Directory Migration With Tests

**Files:**
- Modify: `tests/test_marketplace_manifest.py`
- Modify: `plugins/paper-source/tests/test_skill_bundle_contract.py`

- [x] **Step 1: Add failing tests**

Add tests requiring:
- `plugins/paper-source/scripts/build/paper_source/__init__.py`
- `plugins/paper-source/scripts/build/epi/__init__.py` as legacy shim only
- no `plugins/paper-source/scripts/build/epi/artifacts.py`
- `tests/paper_source/` instead of legacy `tests/epi/`
- `plugins/paper-source/skills/paper-source-paper-deposition/`
- `plugins/paper-source/metric-packs/paper-source-quality-gates/`

- [x] **Step 2: Verify red**

Run:

```powershell
python -m pytest tests\test_marketplace_manifest.py::test_paper_source_runtime_package_uses_current_directory_name_with_legacy_shim_only plugins\paper-source\tests\test_skill_bundle_contract.py::test_paper_source_support_directories_use_current_names -q --basetemp .pytest_tmp_stage3a_red
```

Expected: both tests fail because the new directories do not exist yet.

### Task 2: Rename Source-Visible Folders

**Files:**
- Move: `plugins/paper-source/scripts/build/epi` runtime files -> `plugins/paper-source/scripts/build/paper_source`
- Create: `plugins/paper-source/scripts/build/paper_source/__init__.py`
- Keep: `plugins/paper-source/scripts/build/epi/__init__.py` as the only legacy shim
- Move: `tests/epi` -> `tests/paper_source`
- Move: `plugins/paper-source/skills/epi-paper-deposition` -> `plugins/paper-source/skills/paper-source-paper-deposition`
- Move: `plugins/paper-source/metric-packs/epi-quality-gates` -> `plugins/paper-source/metric-packs/paper-source-quality-gates`

- [ ] **Step 1: Verify source and target paths are inside the workspace**

Run `Resolve-Path` for the existing paths and confirm target parents are under `D:\paper-search`.

- [ ] **Step 2: Rename directories**

Use `Rename-Item` for each directory. Keep `plugins/paper-source/scripts/build/epi/` as a new minimal compatibility package.

- [ ] **Step 3: Add compatibility package**

`plugins/paper-source/scripts/build/epi/__init__.py` should extend its package search path to `paper_source` so `import epi.artifacts` still loads the runtime files.

### Task 3: Update Imports And Entrypoints

**Files:**
- Modify: Python files under `plugins/paper-source/scripts/build/paper_source`
- Modify: `plugins/paper-source/scripts/orchestrator.py`
- Modify: `plugins/paper-source/scripts/init_paper_wiki.py`
- Modify: `plugins/paper-source/scripts/paper_search_mcp_launcher.py`
- Modify: tests under `tests/paper_source`

- [ ] **Step 1: Mechanically rewrite Python imports**

Change `from epi.` to `from paper_source.`, `import epi.` to `import paper_source.`, and module-name strings used by tests from `epi.` to `paper_source.` where they test current source names.

- [ ] **Step 2: Keep legacy CLI argv names only where they are historical test inputs or compatibility messages**

Do not remove old artifact schemas or old command flags in this task.

### Task 4: Update Skill, Metric, And Contract Names

**Files:**
- Modify: `plugins/paper-source/skills/routing.yaml`
- Modify: moved `paper-source-paper-deposition` skill files
- Modify: moved metric pack manifest and emitter
- Modify: contract tests referencing the moved paths

- [ ] **Step 1: Update primary references**

Use `paper-source-paper-deposition` and `paper-source-quality-gates` as the current folder and metric pack names.

- [ ] **Step 2: Preserve legacy trigger text**

Keep `epi-wiki-deposition`, `wiki_deposition_task.json`, and old naming only where explicitly described as legacy compatibility.

### Task 5: Update New Vault Runtime Names With Compatibility

**Files:**
- Modify: `plugins/paper-source/scripts/build/paper_source/artifacts.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/epi_repository.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/runtime_config.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/cli_parser.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/wiki_ingest_record.py`

- [ ] **Step 1: Add primary Paper Source constants**

Add primary `_paper_source/`, `PAPER_SOURCE_RUNTIME_CONFIG`, and `paper-source-*` schema names while keeping old names accepted.

- [ ] **Step 2: Prefer new writes and read legacy fallbacks**

New bootstrap writes `_paper_source/`; existing `_epi/` is still read.

- [ ] **Step 3: Add Paper Wiki record request names**

Accept both `paper-wiki-record-request-v1` and `prw-record-request-v1`; prefer `paper-wiki-record-request.json` in new run state.

### Task 6: Verify And Commit

**Files:**
- All files changed by Tasks 1-5

- [ ] **Step 1: Run focused tests**

```powershell
python -m pytest tests\paper_source\test_wiki_init.py tests\paper_source\test_runtime_config.py tests\paper_source\test_wiki_ingest_record.py plugins\paper-source\tests\test_skill_bundle_contract.py tests\test_marketplace_manifest.py -q --basetemp .pytest_tmp_stage3a
```

- [ ] **Step 2: Run cross-plugin contract tests**

```powershell
python -m pytest tests\paper_research_wiki\test_plugin_contract.py tests\test_marketplace_manifest.py -q --basetemp .pytest_tmp_stage3a_contract
```

- [ ] **Step 3: Check whitespace and stage exact files**

Run `git diff --check`, inspect `git status --short`, and stage only intended files. Leave `.claude/` untracked.
