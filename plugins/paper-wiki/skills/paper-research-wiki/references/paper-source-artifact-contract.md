# Paper Source Artifact Contract

canonical handoff:

- `wiki-ingest-brief.json`

Required source inputs for Paper Wiki deposition:

- `briefs/reading-report.md`
- `metadata.json`
- `paper.pdf`
- MinerU Markdown, images, manifest, `figure-index.json`, `formula-index.json`, and `asset-normalization-record.json`

MinerU Markdown is the primary source for formulas, notation, method context, and prose. Native TeX is not required for Paper Wiki deposition, and missing `mineru/paper.tex` must not block formal writing or record readiness. Use the PDF, `formula-index.json`, `figure-index.json`, and image evidence as fallback checks only when MinerU Markdown is missing, wrong, ambiguous, or insufficient. Optional aids are non-empty native `mineru/paper.tex` when present, reader evidence maps, claim support JSON, critic reports, and `wiki-agent-trigger.json`.

Paper Source owns paper-level deduplication before handoff. Paper Wiki treats incoming handoffs as new papers and performs graph-level merge-before-create against existing formal knowledge pages.

Paper Source owns `paper-gate`, human approval records, and `record-wiki-ingest`.
