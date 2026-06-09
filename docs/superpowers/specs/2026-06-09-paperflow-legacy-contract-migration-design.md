# PaperFlow Legacy Contract Migration Design

- Date: 2026-06-09
- Status: Approved in conversation for Stage 3A compatibility migration
- Scope: Source-repo contract migration for Paper Source and Paper Wiki naming

## Purpose

Stage 1 made the user-visible names `Paper Source` and `Paper Wiki`.
Stage 2 hard-cut the installable plugin machine names to `paper-source` and `paper-wiki`, but deliberately left legacy runtime and artifact contracts such as `_epi/`, `EPI_VAULT`, `epi-*` schema names, `prw-record-request.json`, and the Python `epi` import shim in place.

Stage 3A moves those remaining machine-facing contracts toward current PaperFlow names without breaking existing vaults. New source-generated artifacts should use Paper Source and Paper Wiki naming, while existing legacy artifacts remain readable through a compatibility layer.

## Locked Decisions

| Contract area | New primary naming | Legacy readable naming |
| --- | --- | --- |
| Paper Source vault root | `_paper_source/` | `_epi/` |
| Paper Source env vars | `PAPER_SOURCE_VAULT`, `PAPER_SOURCE_RUNTIME_CONFIG` | `EPI_VAULT`, `EPI_RUNTIME_CONFIG` |
| Paper Source schema prefix | `paper-source-*` | `epi-*` |
| Paper Wiki schema prefix | `paper-wiki-*` | `prw-*` |
| Paper Wiki record request file | `paper-wiki-record-request.json` | `prw-record-request.json` |
| Python/internal namespace | `paper_source`, `paper_wiki` for new code | `epi` import compatibility |
| Compatibility deposition skill | Paper Source deposition compatibility adapter | `paper-source-paper-deposition` skill id |

## Scope

Stage 3A changes the source repository only. It does not directly migrate the real `D:\paper-research-wiki` vault.

Stage 3A should:

- introduce named constants/helpers for primary and legacy Paper Source roots, env vars, schema versions, and record-request filenames
- make new Paper Source runs write `_paper_source/` artifacts by default
- make readers prefer `_paper_source/` and fall back to `_epi/` when the new root is absent
- make runtime config prefer `PAPER_SOURCE_RUNTIME_CONFIG` and fall back to `EPI_RUNTIME_CONFIG`
- make default vault detection prefer `PAPER_SOURCE_VAULT` and fall back to `EPI_VAULT`
- make new schemas use `paper-source-*` and `paper-wiki-*`
- continue accepting legacy `epi-*` and `prw-*` schema values where existing artifacts are consumed
- make Paper Wiki write `paper-wiki-record-request.json` for new readiness requests
- continue consuming legacy `prw-record-request.json`
- update user-visible docs, skills, workflow prose, and plugin descriptions so `EPI` and `PRW` appear only as explicitly legacy/internal compatibility terms
- keep tests explicit about which old names are allowed because they are legacy contracts

Stage 3A may introduce lightweight `paper_source` wrappers or facades for new code, but it does not need to physically rename every Python file in `scripts/build/paper_source` in the first implementation pass. A full package relocation is a later stage after the compatibility layer is tested.

## Non-Goals

- Do not directly modify, rename, or clean `D:\paper-research-wiki`.
- Do not delete legacy `_epi/` read support.
- Do not remove support for `EPI_VAULT` or `EPI_RUNTIME_CONFIG`.
- Do not break existing `epi-*` or `prw-*` artifacts.
- Do not remove `paper-source-paper-deposition` until a replacement skill id and migration path are proven.
- Do not treat external `paper-search-mcp`, `paper-search` CLI, or repository URL strings as legacy plugin names.
- Do not bulk-replace substrings inside historical audit files, migration notes, schema constants, or tests without checking whether they are compatibility evidence.

## Compatibility Model

Paper Source has a primary root and a legacy root:

- Primary root: `<vault>/_paper_source`
- Legacy root: `<vault>/_epi`

Read behavior:

1. If `_paper_source/` exists, read it as the primary source repository.
2. If `_paper_source/` is absent and `_epi/` exists, read `_epi/` as a legacy Paper Source repository.
3. If both exist, prefer `_paper_source/` for new state and consult `_epi/` only through explicit legacy lookup paths.
4. Diagnostics must report both roots so users can see whether they are in migrated, legacy-only, or mixed state.

Write behavior:

1. New runs write only `_paper_source/` unless a command is explicitly operating on a legacy artifact for migration or verification.
2. New schemas use `paper-source-*` or `paper-wiki-*`.
3. Legacy schema readers remain tolerant and report legacy status instead of failing solely because an old schema prefix is present.
4. No command silently rewrites a legacy vault tree in place. Vault conversion requires an explicit migration command with dry-run and backup guidance.

## Migration Command Shape

Stage 3A should include or prepare a migration command surface such as:

```powershell
python scripts\orchestrator.py paper-source-repository-migrate --vault <vault> --preview --json
python scripts\orchestrator.py paper-source-repository-migrate --vault <vault> --json
```

The preview mode should report:

- whether `_paper_source/` exists
- whether `_epi/` exists
- which legacy artifact classes would move or copy
- schema versions that would be rewritten
- record request files that would be renamed
- files that would be left as historical evidence
- whether the vault has dirty Git state
- the required backup or snapshot path before a real migration

The real migration command must be conservative. It should refuse to run without an explicit confirmation flag or phrase, and it should write a manifest that records source paths, target paths, hashes, counts, and skipped historical files.

## Documentation Rules

Use `Paper Source` and `Paper Wiki` for user-facing plugin names.

Use `paper-source` and `paper-wiki` for plugin ids and marketplace paths.

Use `paper_source` and `paper_wiki` for new Python-facing identifiers where an underscore identifier is required.

Use `EPI`, `PRW`, `epi`, and `prw` only when one of these is true:

- the text names a legacy artifact, schema, env var, Python package, or compatibility skill
- the text explains a migration path from an old contract to a new one
- the text describes historical caches, historical audit artifacts, or pre-Stage-3 behavior
- the text protects compatibility tests that intentionally load old fixtures

Every remaining old-name occurrence in user-facing docs should be either removed or explicitly labelled as legacy/internal compatibility.

## Error Handling

Mixed roots are valid but must be visible:

- `status=primary` when `_paper_source/` exists and no legacy root is needed
- `status=legacy_fallback` when only `_epi/` exists
- `status=mixed` when both roots exist
- `status=missing` when neither root exists

Commands that write new artifacts should fail if they would accidentally write to `_epi/` as the primary path after Stage 3A, except for explicit compatibility or migration commands.

Commands that read legacy artifacts should preserve their original schema value in reports and should not claim that a legacy artifact has been migrated unless a migration manifest exists.

## Test Impact

Focused tests should cover:

- new root helpers prefer `_paper_source/`
- legacy root helpers fall back to `_epi/`
- env resolution prefers `PAPER_SOURCE_*` and falls back to `EPI_*`
- new runs write `paper-source-*` schema values
- legacy `epi-*` artifacts remain readable
- Paper Wiki writes `paper-wiki-record-request.json`
- legacy `prw-record-request.json` remains consumable
- docs/tests reject unlabelled user-facing `EPI` / `PRW` wording outside allowed legacy/internal contexts
- migration preview reports planned changes without writing

Expected verification starts with focused tests around the changed modules, then expands to current Paper Source and Paper Wiki contract suites:

```powershell
python -m pytest tests\paper_source tests\paper_research_wiki tests\test_marketplace_manifest.py -q
git diff --check
```

If the implementation touches plugin manifests or installed-cache expectations, plugin validation should run against both source plugin roots. Installed runtime verification remains separate from source-repo validation.

## Acceptance Criteria

- New Paper Source code paths write `_paper_source/` by default.
- Existing `_epi/` vaults remain readable.
- New env vars are documented and preferred; old env vars still work as fallback.
- New generated schemas use `paper-source-*` and `paper-wiki-*`.
- Legacy `epi-*` and `prw-*` schemas remain accepted in readers.
- New Paper Wiki readiness requests use `paper-wiki-record-request.json`.
- Legacy `prw-record-request.json` remains accepted by Paper Source record commands.
- User-facing docs lead with Paper Source and Paper Wiki.
- Remaining `EPI` / `PRW` references are explicitly legacy/internal compatibility, historical evidence, or current code/package compatibility.
- No command in this stage directly migrates the real `D:\paper-research-wiki` vault without an explicit later migration run.

## Follow-Up Stage

Stage 3B can consider deeper schema retirement after Stage 3A passes source and compatibility tests. Candidate follow-up work includes:

- removing internal imports of the legacy `epi` package where compatibility no longer needs them
- retiring remaining `epi-*` schema names behind explicit migration readers
- introducing a replacement skill id for `paper-source-paper-deposition`
- retiring legacy env vars after at least one migration window
- migrating `D:\paper-research-wiki` through a dedicated dry-run, snapshot, manifest, and rollback procedure
