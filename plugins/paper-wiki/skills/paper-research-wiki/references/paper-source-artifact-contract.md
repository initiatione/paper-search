# Paper Source Artifact Contract

canonical handoff:

- `wiki-ingest-brief.json`

legacy compatibility artifact:

- `wiki_deposition_task.json` (deprecated compatibility)

Required source inputs for Paper Wiki deposition:

- `briefs/reading-report.md`
- `metadata.json`
- `paper.pdf`
- MinerU Markdown, TeX, images, and manifest

Optional aids are reader evidence maps, claim support JSON, critic reports, and `wiki-agent-trigger.json`.

Paper Wiki must not treat task-only legacy handoffs as ready. Do not treat task-only legacy handoffs as ready. If `wiki_deposition_task.json` exists without `wiki-ingest-brief.json`, report the legacy limitation and route back to Paper Source to regenerate or repair the brief before formal writes.

Paper Source owns `paper-gate`, human approval records, and `record-wiki-ingest`.
