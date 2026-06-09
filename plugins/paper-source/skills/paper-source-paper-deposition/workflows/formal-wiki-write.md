# Formal Wiki Write Compatibility Adapter

Use this workflow only when a legacy Paper Source deposition request names legacy `wiki_deposition_task.json`, `_epi/`, or `epi-wiki-deposition`.

## Load Inputs

1. Locate `_paper_source/staging/papers/<slug>/wiki-ingest-brief.json`.
2. If `wiki-ingest-brief.json` is missing and only `wiki_deposition_task.json` exists, stop and route back to Paper Source to regenerate or repair the brief.
3. If the request points to legacy `_epi/`, treat it only as a read compatibility input and route back to Paper Source to regenerate the current `_paper_source/` brief.
4. Read the target vault `AGENTS.md` and `_meta/*` contract files when present.

## Route

Invoke Paper Wiki `$paper-research-wiki` for formal paper wiki work. Paper Wiki owns source-first deposition, graph-aware rewrite, provenance, language, link repair, QMD boundary reporting, `final-source-review.json`, and post-task checks.

This compatibility adapter does not duplicate Paper Wiki page-family, frontmatter, language, or lint rules. It only preserves compatibility with old Paper Source artifact names.

Internal `_paper_source/` and legacy `_epi/` pages must not enter the formal graph.
