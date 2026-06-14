# Formal Wiki Write Handoff Cleanup

Use this workflow only when a historical Paper Source deposition request names `wiki_deposition_task.json` and needs to be regenerated into the current `wiki-ingest-brief.json` handoff.

## Load Inputs

1. Locate `_paper_source/staging/papers/<slug>/wiki-ingest-brief.json`.
2. If `wiki-ingest-brief.json` is missing and only `wiki_deposition_task.json` exists, stop and route back to Paper Source to regenerate or repair the brief.
3. Read the target vault `AGENTS.md` and `_meta/*` contract files when present.

## Route

Invoke Paper Wiki `$paper-research-wiki` for formal paper wiki work. Paper Wiki owns source-first deposition, graph-aware rewrite, provenance, language, link repair, QMD boundary reporting, `final-source-review.json`, and post-task checks.

This cleanup workflow does not duplicate Paper Wiki page-family, frontmatter, language, or lint rules. It only helps move retired task-file requests back to the current handoff.

Internal `_paper_source/` pages must not enter the formal graph.
