---
name: zotero-sync
description: "Use when recording or explicitly running the EPI Zotero synchronization stage for a paper. The default path writes an auditable local zotero-record.json and skips external Zotero writes unless enabled."
---

# Zotero Sync

Zotero sync is optional and explicit.

Record a skipped Zotero stage:

```powershell
python scripts\orchestrator.py zotero-sync --paper-root D:\paper-research-wiki\_raw\papers\<paper-slug> --collection EPI
```

Record an enabled fixture sync:

```powershell
python scripts\orchestrator.py zotero-sync --paper-root D:\paper-research-wiki\_raw\papers\<paper-slug> --collection EPI --enabled --item-key <zotero-item-key>
```

The output is `zotero-record.json` under the paper raw artifact directory.
