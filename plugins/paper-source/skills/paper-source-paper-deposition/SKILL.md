---
name: paper-source-paper-deposition
description: >
  Use when cleaning up retired Paper Source handoff artifacts or regenerating current wiki-ingest-brief.json handoffs from historical task files；用于历史 handoff 修复、retired handoff cleanup、重建 wiki-ingest-brief。
---

# Paper Source Paper Deposition

Use this skill only when a historical Paper Source handoff artifact must be inspected, archived, or regenerated into the current `wiki-ingest-brief.json` path.

Canonical path: formal paper wiki work goes through Paper Wiki `$paper-research-wiki` using `_paper_source/staging/papers/<slug>/wiki-ingest-brief.json` as the handoff.

Retired handoff cleanup: if only `wiki_deposition_task.json` exists, ask Paper Source to regenerate or repair `wiki-ingest-brief.json` before formal writes. Do not start new formal wiki work from retired task files or old alias names.

## Workflow Routing

| Intent | Load |
| --- | --- |
| User-facing formal paper wiki writing, extraction, checks, updates, relinking, or graph-aware rewrite | `$paper-research-wiki` from Paper Wiki |
| Historical `wiki_deposition_task.json` cleanup or regeneration | `workflows/formal-wiki-write.md` |

## Boundaries

- Paper Source source bundles and `_paper_source/` artifacts are evidence inputs, not formal wiki pages.
- Paper Source owns `paper-gate`, human approval records, and `record-wiki-ingest`.
- Paper Wiki owns formal page writing, graph-aware rewrite, provenance sidecars, language gate, link repair, and post-task checks.
- Internal `_paper_source/` pages must not enter the formal graph.
