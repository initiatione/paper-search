---
name: epi-paper-deposition
description: "Use when turning EPI source bundles or wiki_deposition_task.json files into formal Obsidian/LLM Wiki staging pages. This is the required adapter between EPI's paper evidence pipeline and the obsidian-wiki skill layer; use it whenever an EPI handoff, wiki ingest trigger, final paper deposition, formula derivation page, synthesis page, or seven-family EPI paper wiki write is requested."
---

# EPI Paper Deposition

Use this skill at the boundary where EPI stops being a paper evidence engine and the wiki layer starts writing formal knowledge. EPI Core prepares source bundles and audit artifacts under `_epi/`; this adapter reads `wiki_deposition_task.json` and coordinates the formal wiki skills.

Compatibility note: older EPI artifacts may say `epi-wiki-deposition`. Treat that as an alias for this skill.

## Required Inputs

Load these before writing or staging formal pages:

- `_epi/staging/papers/<slug>/wiki_deposition_task.json`
- `_epi/staging/papers/<slug>/wiki-ingest-brief.json`
- `_epi/staging/papers/<slug>/briefs/reading-report.md`
- `_epi/raw/papers/<slug>/metadata.json`
- `_epi/raw/papers/<slug>/paper.pdf`
- `_epi/raw/papers/<slug>/mineru/<slug>.md`
- `_epi/raw/papers/<slug>/mineru/paper.tex`
- `_epi/raw/papers/<slug>/mineru/images/*`
- `_epi/raw/papers/<slug>/mineru/mineru-manifest.json`
- target vault `AGENTS.md` and `_meta/*` contract files

Reader and critic files reduce reading cost when present. They are not source authority.

## Skill Stack

Use the obsidian-wiki layer explicitly:

- `llm-wiki` for the wiki architecture and source-first knowledge compilation pattern.
- `wiki-context-pack` before writing, so existing related pages are read first.
- `wiki-ingest` for staged page creation and merge decisions.
- `wiki-lint` before record or stage commit.
- `wiki-stage-commit` for human-reviewed promotion from staged writes.
- `wiki-status` and `wiki-query` when checking existing knowledge or pending staged pages.
- `wiki-provenance` for claim support, evidence addresses, and final-source-review closure.
- `tag-taxonomy` for tags and aliases.

Quality enhancement skills such as `wiki-synthesize`, `wiki-dedup`, and `cross-linker` are useful after the first staged pages exist.

## Formal Page Families

Preserve the EPI paper research structure:

- `references/`: single-paper evidence pages with problem, method, formulas, experiments, metrics, limits, and reproduction clues.
- `concepts/`: reusable concepts, variables, assumptions, method variants, and conditions of use.
- `derivations/`: formula derivation pages with variable definitions, original equations, derivation chain, assumptions, control meaning, and cross-paper differences.
- `experiments/`: platforms, simulation or hardware settings, baselines, metrics, environment, and reproducibility risks.
- `synthesis/`: cross-paper matrices, complementarity, contradictions, and evidence strength.
- `reports/`: low-burden Chinese reading entrypoints.
- `opportunities/`: research gaps linked to specific paper limitations, technical routes, and verifiable experiments.

Do not create generic `entities/`, `skills/`, `journal/`, or `projects/` pages for formal EPI deposition unless the target vault contract explicitly routes a secondary copy there.

## Frontmatter Contract

Every formal page must include frontmatter with at least:

```yaml
---
title:
category:
page_family:
tags:
aliases:
sources:
summary:
provenance:
  extracted:
  inferred:
  ambiguous:
base_confidence:
lifecycle:
lifecycle_changed:
tier:
created:
updated:
---
```

Rules:

- `category` and `page_family` match the seven-family directory, such as `derivations`.
- `sources` point to the EPI source bundle artifacts, not only to a reader summary.
- `summary` is short enough for `wiki-query` previews.
- Initial `lifecycle` is `draft` or `review-needed`; do not mark pages `source-reviewed` or `verified` until source review and lint gates pass.
- `provenance.extracted`, `provenance.inferred`, and `provenance.ambiguous` are present even if a list is empty.

## Quality Gates

Before `record-wiki-ingest` or `wiki-stage-commit`, check:

- Required frontmatter fields are present.
- `summary`, `sources`, `provenance`, `category`, `tags`, `base_confidence`, and `tier` are not empty.
- Formal pages use Obsidian wikilinks where internal knowledge is referenced.
- `_epi/` and other internal roots must not enter the formal graph as pages.
- Do not use forbidden formula blocks such as ` ```math`, ` ```tex`, or ` ```latex`; use `$...$` or `$$...$$`.
- `derivations/` pages include variable definitions and a derivation chain.
- `references/` pages include more than an abstract: model or method, formulas, experiments, metrics, and limitations.
- `synthesis/` pages include a cross-paper comparison matrix.
- `concepts/` pages are reusable concept pages, not one paper retitled as a concept.

If lint fails, repair staged pages before recording ingest completion.
