# Research Brief Contract

## Minimum Complete Brief

Collect only what Paper Source needs for the current task:

- `slug`: `YYYYMMDD-<topic>` lowercase ASCII kebab-case.
- `title`: short user-facing title.
- `task`: what papers or evidence to find.
- `domain_scope`: hard topical boundaries.
- `specific_questions`: one or more answerable research questions.
- `keywords`: required or high-value search terms.
- `exclusions`: terms, methods, or paper types to avoid.
- `review_policy.type`: `exclude`, `include`, or `mixed`.
- `source_scope.type`: one of the Research Brief source scopes, usually `paper_search_mcp_default`.
- `output_goal.type`: reading priorities, staging candidates, literature-review seed, topic-tracking seed, or fact-check sources.
- `unknowns`: explicit gaps that should remain visible.
- `field_sources`: mark whether each field came from user confirmation, config/repo state, or a brief default.

## Questioning Rules

Ask one decision point per turn. Each question must include:

- a recommended answer;
- why the choice affects Paper Source search, ranking, source-staging, or handoff gates;
- a short fallback such as "use the recommendation" when the user does not care.

Read before asking when available:

- `_paper_source/meta/paper-source-config.yaml`;
- recent `_paper_source/research-briefs/*/research-brief.json`;
- relevant `_paper_source/runs/*/report.json` or `search-record.json`;
- current workspace docs or user-provided files.

There is no fixed round count. Continue only until the minimum complete brief is safe to produce.

## Confirmation And Creation

Before confirmed creation, present a Chinese summary covering task, domain scope, questions, keywords, exclusions, source scope, output goal, and unknowns. Ask for explicit confirmation; do not treat silence or a vague "ok" as confirmation if material fields are still uncertain.

After confirmation, write an answers JSON and run:

```powershell
python scripts\orchestrator.py research-brief create --answers-json <answers.json> --vault <vault> --json
```

The generated `research-brief.md` is Chinese for the user. The generated `agent-brief.md` is English for downstream agents.

## Downstream Boundary

Use the confirmed `research-brief.json` for discovery:

```powershell
python scripts\orchestrator.py dry-run --from-brief <research-brief.json> --vault <vault>
```

Research Briefs override Research Profile for the current task, but they are not Paper Wiki handoffs. They must not write Paper Wiki formal pages directly from a Research Brief. Formal wiki work still goes through source-staging, `wiki-ingest-brief.json`, approval, and Paper Wiki.

Use current terms: Paper Source and Paper Wiki. Old EPI/PRW names are legacy-only if an existing artifact uses them. Paper Source uses `paper-search-mcp`; avoid legacy or alternate backend names.
