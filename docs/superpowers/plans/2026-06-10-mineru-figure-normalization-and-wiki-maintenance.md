# MinerU Figure Normalization And Wiki Maintenance Implementation Plan

> **For agentic workers:** User explicitly requested no TDD flow for this implementation. Implement directly, then run focused verification.

**Goal:** Add Paper Source raw MinerU asset normalization plus a separate Paper Wiki formal-page maintenance skill entrypoint.

**Architecture:** Paper Source owns raw bundle normalization and repair under `_paper_source/raw/<slug>` and legacy `_epi/raw/<slug>`. Paper Wiki owns formal-page audit/repair workflow guidance and must not rename raw assets.

**Tech Stack:** Python standard library, existing Paper Source CLI modules, Markdown workflow docs, YAML routing.

---

### Task 1: Raw Bundle Normalization Core

**Files:**
- Create: `plugins/paper-source/scripts/build/paper_source/asset_normalization.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/run_mineru_parse.py`

- [ ] Implement Markdown image extraction, nearby caption detection, stable filename planning, formula-image classification, dry-run/execute behavior, and JSON records.
- [ ] Call normalization after successful MinerU materialization and fixture materialization.

### Task 2: CLI Entry

**Files:**
- Modify: `plugins/paper-source/scripts/build/paper_source/cli_parser.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/cli_routes.py`
- Modify: `plugins/paper-source/scripts/build/paper_source/cli.py`

- [ ] Add `normalize-mineru-assets --slug <slug> [--execute] [--json]`.
- [ ] Resolve both `_paper_source/raw/<slug>` and legacy `_epi/raw/<slug>`.
- [ ] Print/read JSON result without touching formal wiki pages.

### Task 3: Paper Wiki Maintenance Skill Entry

**Files:**
- Create: `plugins/paper-wiki/skills/paper-research-wiki/workflows/maintain-figures.md`
- Modify: `plugins/paper-wiki/skills/routing.yaml`
- Modify: `plugins/paper-wiki/skills/paper-research-wiki/SKILL.md`

- [ ] Add a formal-page maintenance route that audits and repairs figure/formula evidence by consuming Paper Source indexes.
- [ ] Make the boundary explicit: no raw asset renaming from Paper Wiki.

### Task 4: Verification

- [ ] Run focused parser/CLI import checks.
- [ ] Run focused pytest covering MinerU parse adapter if feasible.
- [ ] Run `git diff --check`.
