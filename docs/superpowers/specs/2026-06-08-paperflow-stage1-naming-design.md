# PaperFlow Stage 1 Naming Design

- Date: 2026-06-08
- Status: Design ready for user review
- Scope: User-visible naming for the existing bundled EPI/PRW plugin family

## Purpose

The current public names are too implementation-oriented: `paper-search` sounds like only retrieval, `EPI` is opaque, and `PRW` is an abbreviation that users must learn before they understand the workflow.

The long-term product model is one bundle with two cooperating plugins. Stage 1 changes the user-visible naming so that the workflow reads naturally, while preserving the current machine-facing identifiers for compatibility.

## Locked Decisions

| Concept | Stage 1 name | Machine-facing name in stage 1 |
| --- | --- | --- |
| Bundle/product | PaperFlow | `paper-search` |
| Source preparation plugin | Paper Source | `epi` |
| Wiki maintenance plugin | Paper Wiki | `prw` |

Conversational aliases:

- `PS` means Paper Source.
- `PW` means Paper Wiki.
- `PS` and `PW` are natural-language aliases only. They are not separate plugin names, manifest names, skill names, or explicit `$PS` / `$PW` entrypoints.

Legacy names:

- `EPI` remains a compatibility alias for Paper Source for at least one minor version cycle.
- `PRW` remains a compatibility alias for Paper Wiki for at least one minor version cycle.

## Stage 1 Goals

1. Make user-visible copy lead with PaperFlow, Paper Source, and Paper Wiki.
2. Keep `epi` and `prw` as plugin `name` values, installed-cache identifiers, directory names, test anchors, and artifact compatibility terms.
3. Update plugin manifest display names, short descriptions, long descriptions, default prompts, README text, and user-facing skill descriptions where they shape user routing.
4. Add clear legacy wording: "Paper Source, formerly EPI" and "Paper Wiki, formerly PRW" where users might see both names.
5. Support conversational routing phrases such as "用 PS 找论文" and "用 PW 沉淀到 wiki" without creating new machine entrypoints.
6. Keep artifact and contract language precise when old names still denote machine fields or historical compatibility.

## Non-Goals

- Do not rename plugin directories: `plugins/epi` and `plugins/PRW` stay in place.
- Do not change marketplace plugin `name` values from `epi` / `prw`.
- Do not rename skill directories, Python modules, CLI commands, MCP server names, artifact paths, or schema fields.
- Do not migrate installed cache, user config, or runtime registrations.
- Do not replace every `EPI` / `PRW` occurrence mechanically.
- Do not add wrapper plugins, third plugins, `$PS`, or `$PW`.

## Naming Rules

Use PaperFlow when describing the bundle or product-level workflow.

Use Paper Source for the first plugin when the topic is user-facing source preparation: paper discovery, acquisition, MinerU parsing, source bundle preparation, approval handoff, and record closure.

Use Paper Wiki for the second plugin when the topic is formal wiki work: deposition, read-only wiki questions, formal page checks, rewrites, relinking, language gate, QMD boundary reporting, and record readiness reporting.

Use EPI and PRW only when one of these applies:

- The text is naming a current machine-facing identifier, path, installed plugin name, or command surface.
- The text is explaining legacy aliases or compatibility.
- The text is describing historical artifacts, schemas, test fixtures, or existing field names.
- The text needs to say that Paper Source was formerly EPI or Paper Wiki was formerly PRW.

Use PS/PW only as conversational examples or trigger phrases, never as source-of-truth identifiers.

## Plugin Manifests

Stage 1 should update:

- `marketplace.json` and `.agents/plugins/marketplace.json`
  - `interface.displayName`: `PaperFlow`
  - keep marketplace `name`: `paper-search`
  - keep plugin entries `name`: `epi`, `prw`

- `plugins/epi/.codex-plugin/plugin.json`
  - keep `name`: `epi`
  - `interface.displayName`: `Paper Source`
  - copy should say Paper Source prepares evidence-backed paper source bundles for Paper Wiki
  - mention `formerly EPI` where useful
  - keep version prefix in `shortDescription`

- `plugins/PRW/.codex-plugin/plugin.json`
  - keep `name`: `prw`
  - `interface.displayName`: `Paper Wiki`
  - copy should say Paper Wiki writes, asks, checks, repairs, and maintains formal paper wiki knowledge
  - mention `formerly PRW` where useful
  - keep version prefix in `shortDescription`

## Docs And Skills

Update user-facing docs first:

- `README.md`
- `docs/plugin-development.md`
- `plugins/epi/docs/workflow.md`
- `plugins/epi/docs/structure.md`
- `plugins/epi/docs/epi-linkage.md`
- `plugins/PRW/docs/workflow.md`
- `plugins/PRW/docs/structure.md`
- `plugins/PRW/docs/epi-integration.md`

Update skill routing only where user trigger matching improves:

- Paper Source skills may include natural triggers such as `PS`, `Paper Source`, and `用 PS 找论文`.
- Paper Wiki skills may include natural triggers such as `PW`, `Paper Wiki`, and `用 PW 沉淀到 wiki`.
- Keep `$paper-research-wiki`, `paper-research-wiki`, `epi-paper-deposition`, `wiki-ingest-brief.json`, and other machine/compatibility terms unchanged.

Do not bulk-edit all references files. References that describe artifact contracts may continue using EPI/PRW when those are compatibility or machine terms.

## Boundary Rules

Paper Source does not fail its source workflow because Paper Wiki is absent. Missing Paper Wiki is a capability gap, not an EPI/Paper Source source-staging failure.

Paper Wiki diagnoses missing Paper Source-owned vault bootstrap or source artifacts and points back to Paper Source/EPI. It does not initialize, reset, repair, or silently create EPI-owned structures.

PaperFlow remains a bundle/product name, not a third wrapper plugin.

## Test Impact

Expected test updates:

- Marketplace manifest tests should expect `PaperFlow`, `Paper Source`, and `Paper Wiki` in display/copy fields while still expecting plugin entries `epi` and `prw`.
- PRW contract tests should accept new user-facing naming and retain old machine compatibility assertions.
- EPI current-doc tests should assert the new names in user-facing docs and preserve legacy compatibility statements.

Verification should include:

```powershell
python -m pytest tests\paper_research_wiki\test_plugin_contract.py plugins\epi\tests\test_skill_bundle_contract.py tests\test_marketplace_manifest.py tests\epi\test_current_docs.py -q
python -m json.tool plugins\epi\.codex-plugin\plugin.json > $null
python -m json.tool plugins\PRW\.codex-plugin\plugin.json > $null
python -m json.tool marketplace.json > $null
python -m json.tool .agents\plugins\marketplace.json > $null
git diff --check
```

If plugin validation is part of the implementation pass, run the configured plugin validator against both source plugin directories and report source-vs-installed-cache scope separately.

## Acceptance Criteria

- Users see PaperFlow as the bundle display name.
- Users see Paper Source and Paper Wiki as the two plugin display names.
- User-facing docs explain `Paper Source, formerly EPI` and `Paper Wiki, formerly PRW`.
- `PS` and `PW` appear only as conversational aliases.
- Existing machine-facing names remain unchanged in stage 1: `paper-search`, `epi`, `prw`, `plugins/epi`, `plugins/PRW`.
- No new wrapper plugin or alias plugin is introduced.
- Tests protect both the new user-facing names and the legacy compatibility layer.

## Stage 2 Handoff

Stage 2 may rename machine-facing identifiers after Stage 1 has shipped and compatibility has been observed for at least one minor version cycle. Stage 2 must be a separate design because it touches install names, cache paths, directory names, tests, historical artifacts, and user config.
