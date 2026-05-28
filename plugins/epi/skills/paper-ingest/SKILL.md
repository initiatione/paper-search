---
name: paper-ingest
description: "Use when ingesting one selected engineering paper into EPI raw artifacts, reader outputs, critic reports, and staging drafts. Phase 2 uses local or fixture inputs and must not write compiled wiki pages."
---

# Paper Ingest

Use this skill for Phase 2 one-paper ingest after a paper has been selected.

Fixture command from the plugin root:

```powershell
python scripts\orchestrator.py ingest-one --candidate D:\codex-tmp\candidate.json --pdf D:\codex-tmp\paper.pdf --mineru-md D:\codex-tmp\paper.md --mineru-tex D:\codex-tmp\paper.tex --vault D:\paper-research-wiki
```

For resumable URL-based ingestion, advance one paper by one safe stage at a time:

```powershell
python scripts\orchestrator.py advance-paper --candidate D:\codex-tmp\candidate.json --vault D:\paper-research-wiki
```

For a ranked candidate list, advance each selected paper by one safe stage and keep the per-call budget explicit:

```powershell
python scripts\orchestrator.py advance-batch --candidates D:\codex-tmp\ranked-candidates.json --max-papers 3 --vault D:\paper-research-wiki
```

To continue directly from a dry-run run directory, use its `run_id`:

```powershell
python scripts\orchestrator.py advance-ranked --run-id <dry-run-id> --max-papers 3 --vault D:\paper-research-wiki
```

Outputs are written to:

- `D:\paper-research-wiki\_raw\papers\<paper-slug>\`
- `D:\paper-research-wiki\_staging\papers\<paper-slug>\`
- `D:\paper-research-wiki\_runs\<run-id>\` for batch advance records

The hard gate remains: No critic pass, no compiled wiki write.

Use redo commands when raw artifacts need recovery:

```powershell
python scripts\orchestrator.py redo-parse --slug <paper-slug> --mineru-md D:\codex-tmp\paper.md --reason "redo parse"
python scripts\orchestrator.py redo-read --slug <paper-slug> --reason "reader stale"
python scripts\orchestrator.py recritic --slug <paper-slug> --reason "reader revised"
```

Redo events are appended to `_raw\papers\<paper-slug>\redo-records.jsonl`.

Phase 2 does not write:

- `D:\paper-research-wiki\references\`
- `D:\paper-research-wiki\concepts\`
- `D:\paper-research-wiki\synthesis\`
