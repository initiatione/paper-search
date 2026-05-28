---
name: paper-discovery
description: "Use when searching, normalizing, filtering, and ranking engineering papers for robotics, AI, embodied intelligence, control, navigation, or motion-control research. Phase 1 defaults to dry-run mode and does not download PDFs, parse with MinerU, write compiled wiki pages, or write Zotero."
---

# Engineering Paper Discovery

Use this skill for Phase 1 paper discovery dry-runs.

Default command from the plugin root:

```powershell
python scripts\orchestrator.py dry-run --query "robotics embodied intelligence control" --max-results 20 --vault D:\paper-research-wiki
```

Outputs are written to:

`D:\paper-research-wiki\_runs\<run-id>\`

Expected dry-run artifacts:

- `run-state.json`
- `search-record.json`
- `normalized.json`
- `filter-report.json`
- `rank.json`
- `report.md`
- `report.json`

Live runs also retain the upstream CLI JSON at `paper-search-raw.json` and point to it from `search-record.json`.

Dry-run mode must stop before acquisition, MinerU parsing, reader generation, critic, wiki promotion, and Zotero.
