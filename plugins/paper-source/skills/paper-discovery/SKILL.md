---
name: paper-discovery
description: >
  Use when Paper Source / PS should search papers: "找最新论文", "找高质量论文", dry-run, rank.
---

# Academic Paper Discovery

Use for Paper Source / PS discovery and reading-priority ranking. Route search, normalize/filter/classify/rank, and reports here; hand off parse, reader/critic, and final wiki work to the routed skill.

Ongoing monitoring, deltas, backlog, or coverage use `topic-tracking` as the outer workflow.

If config is missing, stop and use `config-setup`. See `docs\config.md`.

The full Paper Source chain stays documented in `docs\paper-source-linkage.md`; this skill only owns discovery and ranking.

## Rules

- Discovery is profile-driven; do not treat `paper_search_mcp` result order as quality.
- Paper Source is field-agnostic. Do not hardcode robotics, AUV, AI, medicine, or any other discipline unless present in config/request.
- Derive query plan, `domain_focus_terms`, exclusions, `venue_prior`, and recommendations from `_paper_source\meta\paper-source-config.yaml` plus the current request.
- Use `research_mode`, `paper_classification`, and `ranking_rubric` as routing/explanation contracts.
- For chat results, load `references/output-format.md` and report in reading-priority order with a short Chinese abstract, citation count, impact factor/quartile, CiteScore, or `未核实`.
- EasyScholar is default-on in `dry-run`; missing key/no match/timeout/API error is `未核实`, not guessed.

## Workflow Routing

| Intent | Load |
| --- | --- |
| One-off dry-run, query planning, report existing run, or evidence check | `workflows/run-discovery.md` |
| High-quality/latest/non-review discovery that needs high recall before precision filtering | `workflows/multi-source-discovery.md` |
| Prepare PDFs, MinerU artifacts, and source-staging handoff from a ranked run | `paper-ingest/workflows/prepare-ranked.md` |
| Track deltas across prior runs, backlog, coverage gap, or library duplicates | `topic-tracking/SKILL.md` |
| Formal wiki deposition after source-staging and approval | Paper Wiki `$paper-research-wiki`; compatibility fallback `paper-source-paper-deposition/SKILL.md` |

## Reference Routing

Load only what is needed:

- Planning/modes/taxonomy: `references/query-planner.md`, `references/mode-routing.md`, `references/paper-type-taxonomy.md`
- Search/source/dedup/venue: `references/search-protocol.md`, `references/source-tiers.md`, `references/dedup-engine.md`, `references/venue-prior.md`
- Recall/ranking/quality/output: `references/two-stage-retrieval.md`, `references/ranking-rubric.md`, `references/quality-gate.md`, `references/output-format.md`
- Expansion/examples/checks: `references/citation-graph.md`, `references/domain-ontology.md`, `references/anti-patterns.md`, `references/evaluation-set.md`

## Source Boundary

`dry-run` writes only `_paper_source/runs/<run-id>/`. `prepare-ranked` belongs to `paper-ingest` and stops at source-staging. Final pages are written by Paper Wiki `$paper-research-wiki` or compatibility adapter `paper-source-paper-deposition`; discovery never writes them.
