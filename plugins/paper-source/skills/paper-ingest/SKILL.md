---
name: paper-ingest
description: >
  Use when advancing selected Paper Source papers: "推进论文", prepare-ranked, source-staging, approval, wiki handoff.
---

# Paper Ingest

Use after dry-run ranking selects papers. Paper Source / PS chain goal in `docs\paper-source-linkage.md`: high-quality collection, LLM Wiki deposition, low-burden reading report.

If config is missing, stop and use `config-setup`. See `docs\config.md`.

For formal wiki deposition from a Paper Source source bundle, switch to Paper Wiki `$paper-research-wiki` using `wiki-ingest-brief.json`, the canonical Paper Source-to-Paper Wiki handoff. `wiki_deposition_task.json is legacy` compatibility only; use `paper-source-paper-deposition` only for legacy task or `epi-wiki-deposition` mentions. external wiki skills are optional helpers / policy references.

## Reference Routing

Load `references/source-first-reading.md` for reader outputs, critic inputs, staging bundles, or wiki-ingest handoffs. Parse quality is a source bundle check: inspect Markdown, TeX, images, and MinerU manifest.

## Workflow Routing

| Intent | Load |
| --- | --- |
| Download selected ranked papers, run MinerU, write source artifacts, and prepare source-staging | `workflows/prepare-ranked.md` |
| Add reader or critic outputs for important, complex, contradictory, reproducibility, review, or project-decision papers | `workflows/prepare-ranked.md` |
| Show approval report, record human approval, create wiki-agent trigger, or record final wiki ingest | `workflows/approval-and-trigger.md` |
| Formal page writing after `wiki-ingest-brief.json` exists | Paper Wiki `$paper-research-wiki`; fallback compatibility path `paper-source-paper-deposition/workflows/formal-wiki-write.md` only for legacy task mentions |
| Claim labels, provenance blocks, and evidence-address preservation | `wiki-provenance/SKILL.md` |

## Ingest Modes

- `fast-ingest`: default; acquire, MinerU, source artifacts, `_paper_source/staging/papers/<slug>/wiki-ingest-brief.json`, short Chinese reading/approval report.
- `reviewed-ingest`: add reader outputs for poor parse quality, complex formulas/figures, or requested detailed reading.
- `audited-ingest`: add critic outputs for reproduction, literature review, project decisions, or contradictions.

Reader and critic reduce reading cost; they are navigation/audit aids, not source authority. Final wiki prose must read source artifacts.

## Human Approval Boundary

Before final/staged vault writes, show one single concise Chinese-first approval report with Chinese-English terminology and one recommendation: `建议沉淀`, `谨慎沉淀`, or `暂不沉淀`. Record pre-write approval with `record-human-approval --scope run-wiki-ingest-agent`; never ask from raw JSON, gate dumps, path lists, or critic sidecars.

On resume, use `research-queue --bucket ready_to_promote --actions --json` or `wiki-ingest-trigger --slug <slug> --json`. The trigger writes a resume artifact; it does not spawn a hidden agent or write final pages.

## Wiki Boundary

Final Obsidian/LLM Wiki pages are agent-mediated under the target vault contract. Paper Source prepares source bundles, approval, trigger, record artifacts, and `wiki-ingest-brief.json`; it does not write final pages in `references/`, `concepts/`, `derivations/`, `experiments/`, `synthesis/`, `reports/`, or `opportunities/`.

After the wiki ingest agent writes or stages final Markdown pages, create `final-source-review.json`, then record completion with `record-wiki-ingest`. This command is record-only and must not rewrite final pages or replace the target vault's ingest agent.

For ask-mode automation after Paper Wiki completes formal pages, consume `_paper_source/staging/papers/<slug>/paper-wiki-record-request.json` with `record-wiki-ingest --from-paper-wiki-request <request>`. Schema: `paper-wiki-record-request-v1`, `automation_mode=ask`. Paper Wiki writes the request artifact; Paper Source consumes it. Paper Source validates live page hashes, `final-source-review.json`, matching human approval, `paper-gate`, and formal-page rules before writing `wiki-ingest-record.json`. Legacy `prw-record-request.json` remains accepted only for existing artifacts.

If `_paper_source/meta/record-corrections/` marks `correction_type=premature-wiki-ingest-record`, do not treat the old record as final. While status is `pending-paper-wiki-review`, route to Paper Wiki for formal page and `final-source-review.json` repair. After Paper Wiki repairs pages and `final-source-review.json`; Paper Source writes or replaces `wiki-ingest-record.json`: when status is `paper-wiki-reviewed-ready-for-paper-source-record` and `paper-gate` returns `ready_for_wiki_ingest_agent`, rerun `record-wiki-ingest` to replace the premature record.

Paper Source owns vault bootstrap through `wiki-setup`. Paper Wiki consumes the initialized vault contract and should report missing vault structure back to Paper Source instead of creating or resetting the vault itself.
