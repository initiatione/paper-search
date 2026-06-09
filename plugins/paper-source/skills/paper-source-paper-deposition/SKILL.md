---
name: paper-source-paper-deposition
description: >
  Use when handling legacy Paper Source deposition: wiki_deposition_task.json, epi-wiki-deposition, "兼容旧沉淀任务".
---

# Paper Source Paper Deposition

Use this skill only as the legacy compatibility adapter at the Paper Source-to-Paper Wiki boundary, including legacy epi-wiki-deposition mentions.

Canonical path: formal paper wiki work goes through Paper Wiki `$paper-research-wiki` using `_paper_source/staging/papers/<slug>/wiki-ingest-brief.json` as the handoff. Existing legacy `_epi/` handoffs remain readable as compatibility inputs.

Legacy compatibility: older artifacts may say legacy `wiki_deposition_task.json`, `_epi/`, or `epi-wiki-deposition`. Treat those as legacy names and route the user to Paper Wiki after confirming that `wiki-ingest-brief.json` exists. If only the legacy task exists, ask Paper Source to regenerate or repair the brief before formal writes.

## Workflow Routing

| Intent | Load |
| --- | --- |
| User-facing formal paper wiki writing, extraction, checks, updates, relinking, or graph-aware rewrite | `$paper-research-wiki` from Paper Wiki |
| Legacy handoff mentions `wiki_deposition_task.json` or `epi-wiki-deposition` | `workflows/formal-wiki-write.md` |

## Boundaries

- Paper Source source bundles and `_paper_source/` artifacts are evidence inputs, not formal wiki pages; legacy `_epi/` artifacts are read compatibility inputs.
- Paper Source owns `paper-gate`, human approval records, and `record-wiki-ingest`.
- Paper Wiki owns formal page writing, graph-aware rewrite, provenance sidecars, language gate, link repair, and post-task checks.
- Internal `_paper_source/` and legacy `_epi/` pages must not enter the formal graph.
